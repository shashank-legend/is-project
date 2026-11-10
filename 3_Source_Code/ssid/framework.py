"""
The Self-Supervised Intrusion Detection (SSID) framework (Sec. IV of the paper)
and our improved variant SSID+.

Paper components reproduced here (equation numbers refer to the paper):
  * trust coefficient            Gamma = C_rep * C_gen                 (21)
  * representativeness           exponential-KL, normalised            (22)-(32)
  * generalisation               C_gen = 0.5*Delta + 0.5*kappa         (33)-(38)
  * data adequacy                Delta = 1 - min(W / sum|B_k|, 1)      (34)
  * knowledge                    kappa <- 1/2 - 1/2 (E(l) - kappa)     (36)
  * self-supervised selection    p- = Gamma(1-y), p+ = Gamma*y, q = 1-Gamma  (17)-(20)
  * phase switching / update     Gamma >= Theta ends l=0               (14)
                                 Gamma < Theta, |B|>=K, mean y <= gamma -> update (15)
                                 mean y > gamma -> empty B             (16)

SSID+ (team's proposal, switchable flags so each can be ablated):
  * unbiased_kappa : bias-corrected EWMA for kappa (eq. 35 weights sum to <1)
  * rep="js"       : distribution-free, sliding-window Jensen-Shannon
                     representativeness instead of cumulative exponential-KL
  * gate=True      : confidence-gated pseudo-labelling - a packet is accepted
                     as benign only if y_i is below an adaptive bound learned
                     from previously accepted packets (anti-poisoning)
  * forget<1       : forgetting-factor OS-ELM so old traffic fades (drift)
  * adaptive_gamma : intrusion threshold gamma_t = clip(mu + k*sigma) of the
                     IDS outputs on accepted (pseudo-benign) packets, instead
                     of the fixed, scale-dependent gamma = 0.25
"""
from collections import deque
import time
import numpy as np
from .models import ids_output


class _WinHist:
    """Sliding-window histogram with O(1) add/remove."""

    def __init__(self, lo, hi, bins=16, maxlen=3000):
        self.edges = np.linspace(lo, hi, bins + 1)
        self.c = np.zeros(bins); self.q = deque(); self.maxlen = maxlen

    def add(self, v):
        b = int(np.clip(np.searchsorted(self.edges, v) - 1, 0, len(self.c) - 1))
        self.c[b] += 1; self.q.append(b)
        if len(self.q) > self.maxlen:
            self.c[self.q.popleft()] -= 1

    def p(self):
        s = self.c.sum()
        return (self.c + 0.5) / (s + 0.5 * len(self.c))


def _js(p, q):
    m = 0.5 * (p + q)
    return 0.5 * np.sum(p * np.log2(p / m)) + 0.5 * np.sum(q * np.log2(q / m))


class SSID:
    def __init__(self, model, theta=0.95, I=10, K=100, gamma=0.25, seed=0,
                 unbiased_kappa=False, rep="expkl", gate=False, max_batch=5000,
                 refit_every=100, y_untrained=0.5,
                 adaptive_gamma=False, k_sigma=6.0, gamma_min=0.03):
        self.m = model
        self.theta, self.I, self.K, self.gamma = theta, I, K, gamma
        self.rng = np.random.default_rng(seed)
        self.unbiased_kappa, self.rep, self.gate = unbiased_kappa, rep, gate
        self.max_batch, self.refit_every = max_batch, refit_every
        self.y_untrained = y_untrained
        self.adaptive_gamma, self.k_sigma, self.gamma_min = adaptive_gamma, k_sigma, gamma_min

    # ---------------------------------------------------------------- trust
    def _crep(self):
        if self.rep == "expkl":
            if self.n_l < 1 or self.n_o < 1:
                return 0.0
            # lambda = 1/mean(TT), mu = 1/mean(PL); ratio r = lambda_l / lambda_o
            out = 0.0
            for ml, mo in ((self.sum_tt_l / self.n_l, self.sum_tt_o / self.n_o),
                           (self.sum_pl_l / self.n_l, self.sum_pl_o / self.n_o)):
                r = (1 / max(ml, 1e-9)) / (1 / max(mo, 1e-9))
                out += 0.5 * r * np.exp(1 - r)                     # eqs. (28)-(32)
            return float(out)
        # JS on sliding windows of log(TT) and log(PL)
        if len(self.h_tt_l.q) < 1 or len(self.h_tt_o.q) < 1:
            return 0.0
        d = 0.5 * (_js(self.h_tt_o.p(), self.h_tt_l.p()) + _js(self.h_pl_o.p(), self.h_pl_l.p()))
        return float(1.0 - d)

    def _after_update(self, E, n_new):
        self.n_learned += n_new
        delta = 1.0 - min(self.m.n_params / max(self.n_learned, 1), 1.0)       # (34)
        if self.unbiased_kappa:
            self.k_num = 0.5 * self.k_num + 0.5 * E
            self.k_den = 0.5 * self.k_den + 0.5
            self.kappa = 1.0 - self.k_num / self.k_den
        else:
            self.kappa = 0.5 - 0.5 * (E - self.kappa)                          # (36)
        self.cgen = 0.5 * delta + 0.5 * self.kappa                             # (33),(38)
        self.n_updates += 1

    def _learned_add(self, tt, pl):
        self.n_l += 1; self.sum_tt_l += tt; self.sum_pl_l += pl
        if self.rep == "js":
            self.h_tt_l.add(np.log10(tt + 1e-6)); self.h_pl_l.add(np.log10(pl))

    def _observed_add(self, tt, pl):
        self.n_o += 1; self.sum_tt_o += tt; self.sum_pl_o += pl
        if self.rep == "js":
            self.h_tt_o.add(np.log10(tt + 1e-6)); self.h_pl_o.add(np.log10(pl))

    # ---------------------------------------------------------------- run
    def run(self, X, tt, pl, record_every=50):
        n = len(X)
        self.n_l = self.n_o = 0
        self.sum_tt_l = self.sum_pl_l = self.sum_tt_o = self.sum_pl_o = 0.0
        if self.rep == "js":
            mk = lambda lo, hi: _WinHist(lo, hi)
            self.h_tt_l, self.h_tt_o = mk(-6, 1), mk(-6, 1)
            self.h_pl_l, self.h_pl_o = mk(1.7, 3.2), mk(1.7, 3.2)
        self.kappa, self.k_num, self.k_den, self.cgen = 0.0, 0.0, 0.0, 0.0
        self.n_learned = self.n_updates = 0
        self.m_ready = False
        phase, B = 0, deque(maxlen=self.max_batch)
        B0 = []
        acc_y = deque(maxlen=2000)            # y of accepted packets (for the gate)
        y = np.ones(n); s = np.ones(n); G = np.zeros(n); thr = np.full(n, self.gamma)
        g_eff = self.gamma
        ring = deque(maxlen=self.I)
        cache_lo, cache_hi, cache = 0, 0, None
        gamma_t = 0.0
        rec = {"i": [], "gamma": [], "phase": []}
        t0 = time.perf_counter()
        crep_cache, crep_age = 0.0, 999

        for i in range(n):
            # --- detection (unchanged by SSID) ------------------------------
            if self.m_ready:
                if i >= cache_hi:
                    cache_lo, cache_hi = i, min(n, i + 256)
                    cache = ids_output(self.m, X[cache_lo:cache_hi])
                y[i] = cache[i - cache_lo]
            else:
                # no parameters yet: uninformative output. NOTE: with y=1 here,
                # E(0)=1 -> kappa=0, Delta=0 -> Gamma=0 forever (deadlock).
                y[i] = self.y_untrained
            ring.append(y[i]); s[i] = sum(ring) / len(ring)
            thr[i] = g_eff
            attack = s[i] > g_eff
            if phase == 0 or not attack:
                self._observed_add(tt[i], pl[i])

            # --- trust -----------------------------------------------------
            crep_age += 1
            if self.rep == "expkl" or crep_age >= 20:
                crep_cache, crep_age = self._crep(), 0
            gamma_t = crep_cache * self.cgen                                    # (21)
            G[i] = gamma_t

            # --- self-supervised packet selection (17)-(20) ------------------
            if i == 0:
                sel = "benign"
            else:
                u = self.rng.random()
                sel = "benign" if u < gamma_t * (1 - y[i]) else ("malicious" if u < gamma_t else None)
            if sel == "benign" and self.gate and phase >= 1 and len(acc_y) > 50:
                mu, sd = np.mean(acc_y), np.std(acc_y)
                if y[i] > min(self.gamma / 2, mu + 3 * sd):
                    sel = None
            # (malicious-labelled samples are not used by an auto-associative IDS)

            changed = False
            if phase == 0:
                if sel == "benign":
                    B0.append(i); self._learned_add(tt[i], pl[i]); acc_y.append(y[i])
                    k = len(B0)
                    if k == 1 or (k & (k - 1)) == 0 or k % self.refit_every == 0:
                        self.m.fit_initial(X[B0[-3000:]])
                    else:
                        self.m.update(X[i:i + 1])
                    self.m_ready = True; changed = True
                    E = float(np.mean(y[B0[-500:]]))                            # (13)
                    self._after_update(E, 1)
                    gamma_t = self._crep() * self.cgen
                if gamma_t >= self.theta:                                       # (14)
                    phase = 1
            else:
                if sel == "benign":
                    B.append(i)
                if attack:
                    B.clear()                                                   # (16)
                elif gamma_t < self.theta and len(B) >= self.K:                 # (15)
                    idx = np.fromiter(B, int)
                    self.m.update(X[idx]); changed = True
                    for j in idx:
                        self._learned_add(tt[j], pl[j]); acc_y.append(y[j])
                    self._after_update(float(np.mean(y[idx])), len(idx))       # (13)
                    if self.adaptive_gamma:
                        a = np.fromiter(acc_y, float)
                        g_eff = min(self.gamma, max(self.gamma_min, a.mean() + self.k_sigma * a.std()))
                    phase += 1; B.clear()
            if changed:
                cache_hi = 0
            if i % record_every == 0:
                rec["i"].append(i); rec["gamma"].append(gamma_t); rec["phase"].append(phase)

        self.runtime_per_pkt = (time.perf_counter() - t0) / n
        self.m_ready = False
        self.phases = phase
        rec["thr"] = thr
        return y, s, G, rec


# ------------------------------------------------------------------ baselines
def run_offline(model, X, benign_train_idx):
    model.fit_initial(X[benign_train_idx])
    y = ids_output(model, X)
    return y


def run_incremental(model, X, window=750, gamma=0.25, I=10):
    """Periodic retraining every `window` packets on packets the IDS itself
    judged benign; first window assumed benign (cold start), as in Sec. V-C-1."""
    n = len(X)
    model.fit_initial(X[:window])
    y = np.zeros(n)
    y[:window] = ids_output(model, X[:window])
    for st in range(window, n, window):
        en = min(n, st + window)
        y[st:en] = ids_output(model, X[st:en])
        s = smooth(y[max(0, st - I):en], I)[-(en - st):]
        ok = np.where(s <= gamma)[0] + st
        if len(ok) >= 10:
            model.update(X[ok])
    return y


def smooth(y, I=10):
    c = np.concatenate([[0.0], np.cumsum(y)])
    idx = np.arange(len(y))
    lo = np.maximum(0, idx - I + 1)
    return (c[idx + 1] - c[lo]) / (idx + 1 - lo)
