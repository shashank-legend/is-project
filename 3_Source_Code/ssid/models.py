"""
Auto-associative models used as the IDS inside SSID.

AADRNN : Auto-Associative Deep Random Neural Network (Sec. III-A/C of the paper)
         - DRNN cluster activation, eq. (4)
         - hidden layers learned with non-negative L1-regularised least squares
           solved by FISTA, eq. (7), then normalised, eq. (9)
         - output layer learned / updated online with OS-ELM recursive least
           squares, eqs. (10)-(12)
AEMLP  : M-M-M-M sigmoid auto-encoder trained with Adam (Sec. V-C-2).

Both expose the same interface:
    fit_initial(X)   -> full (re)fit on X (initial learning, l = 0)
    update(X)        -> incremental update on a batch (online learning, l >= 1)
    reconstruct(X)   -> X_hat
    n_params         -> number of learnable parameters  (W in eq. 34)
"""
import numpy as np

# ---------------------------------------------------------------- DRNN pieces
P_, R_, LP_, LM_ = 0.05, 0.001, 0.1, 0.01   # p, r, lambda+, lambda-


def zeta(L):
    """Dense-cluster activation, eq. (4). The discriminant can be negative for
    small inputs (the paper does not specify the domain); we clip it to 0."""
    L = np.maximum(L, 0.0)
    a = (P_ * (R_ + LP_) + LM_ + L) / (2.0 * (LM_ + L))
    disc = a * a - LP_ / (LM_ + L)
    return np.clip(a - np.sqrt(np.maximum(disc, 0.0)), 0.0, 1.0)


def _minmax(Z):
    lo, hi = Z.min(0), Z.max(0)
    return (Z - lo) / np.where(hi - lo > 1e-9, hi - lo, 1.0)


def fista_nonneg_l1(A, B, lam=1e-3, iters=150):
    """min_{W>=0} ||A W - B||_F^2 + lam*||W||_1   (FISTA, Beck & Teboulle 2009)."""
    L = 2.0 * np.linalg.norm(A, 2) ** 2 + 1e-9
    W = np.zeros((A.shape[1], B.shape[1])); Y = W.copy(); tk = 1.0
    AtA, AtB = A.T @ A, A.T @ B
    for _ in range(iters):
        G = 2.0 * (AtA @ Y - AtB)
        Wn = np.maximum(Y - (G + lam) / L, 0.0)           # prox of lam|.|_1 + indicator(W>=0)
        tn = (1 + np.sqrt(1 + 4 * tk * tk)) / 2
        Y = Wn + ((tk - 1) / tn) * (Wn - W)
        W, tk = Wn, tn
    return W


def _b(X):
    return np.hstack([X, np.ones((X.shape[0], 1))])


class AADRNN:
    def __init__(self, M=3, H=None, seed=0, ridge=1e-3, forget=1.0):
        self.M, self.H = M, (H or M)
        self.rng = np.random.default_rng(seed)
        self.ridge = ridge
        self.forget = forget          # 1.0 = paper's OS-ELM; <1 = our forgetting-factor variant
        self.Ws = None; self.WH = None; self.O = None
        self.n_params = self.H * (M + 1) * M

    def _raw_hidden(self, X):
        h = (X - self.lo) / self.rg
        for W in self.Ws:
            h = zeta(_b(h) @ W)
        return h

    def _hidden(self, X):
        # Implementation choice (not in the paper): the DRNN cluster activation
        # saturates in a narrow band, so the last hidden layer is standardised
        # with statistics frozen at the last initial fit (numerical conditioning
        # of the least-squares output layer).
        return (self._raw_hidden(X) - self.mu) / self.sd

    def fit_initial(self, X):
        X = np.atleast_2d(X)
        # Frozen input scaling ("adj" step). Implementation choice: with raw
        # [0,1] metrics of small variance the non-negative L1 problem (7)
        # collapses onto the bias row, so inputs are min-max scaled with the
        # statistics of the initial batch.
        self.lo = X.min(0)
        self.rg = np.where(X.max(0) - self.lo > 1e-6, X.max(0) - self.lo, 1.0)
        self.Ws, h = [], (X - self.lo) / self.rg
        for _ in range(self.H - 1):
            WR = self.rng.uniform(0, 1, (self.M, self.M))
            Z = _minmax(zeta(h @ WR)) if len(h) > 1 else zeta(h @ WR)
            W = fista_nonneg_l1(_b(Z), h)                   # eq. (7)
            if not np.any(W[:-1]):                          # degenerate batch
                W[:-1] = np.eye(self.M)
            W = W / max((_b(h) @ W).max(), 1e-6)            # eq. (9)-style scaling
            self.Ws.append(W)
            h = zeta(_b(h) @ W)
        self.mu = h.mean(0)
        self.sd = h.std(0) + 1e-3 if len(h) > 1 else np.ones(self.M)
        Hb = _b((h - self.mu) / self.sd)
        # eq. (10): O0 = (H^T H)^-1  (ridge added - singular for < M+1 samples)
        self.O = np.linalg.inv(Hb.T @ Hb + self.ridge * np.eye(Hb.shape[1]))
        self.WH = self.O @ Hb.T @ X

    def update(self, X):
        """OS-ELM / RLS update of the output layer, eqs. (11)-(12)."""
        X = np.atleast_2d(X)
        Hb = _b(self._hidden(X))
        O = self.O / self.forget
        S = np.eye(len(X)) + Hb @ O @ Hb.T
        O = O - O @ Hb.T @ np.linalg.solve(S, Hb @ O)       # eq. (11)
        self.O = O
        self.WH = self.WH + O @ Hb.T @ (X - Hb @ self.WH)   # eq. (12)

    def reconstruct(self, X):
        return _b(self._hidden(np.atleast_2d(X))) @ self.WH  # eqs. (1)-(3)


class AEMLP:
    """M-M-M-M sigmoid auto-encoder (H = M layers of M neurons), Adam optimiser."""

    def __init__(self, M=3, seed=0, lr=0.01, epochs_init=150, epochs_upd=40, **_):
        rng = np.random.default_rng(seed)
        self.W = [rng.normal(0, 0.5, (M + 1, M)) for _ in range(M)]
        self.lr, self.ei, self.eu = lr, epochs_init, epochs_upd
        self.m = [np.zeros_like(w) for w in self.W]; self.v = [np.zeros_like(w) for w in self.W]
        self.t = 0
        self.n_params = sum(w.size for w in self.W)

    @staticmethod
    def _sig(z):
        return 1 / (1 + np.exp(-z))

    def _fwd(self, X):
        acts = [X]
        for k, W in enumerate(self.W):
            z = _b(acts[-1]) @ W
            acts.append(z if k == len(self.W) - 1 else self._sig(z))
        return acts

    def _train(self, X, epochs):
        X = np.atleast_2d(X)
        for _ in range(epochs):
            acts = self._fwd(X)
            g = 2 * (acts[-1] - X) / len(X)
            self.t += 1
            for k in range(len(self.W) - 1, -1, -1):
                gW = _b(acts[k]).T @ g
                if k > 0:
                    g = (g @ self.W[k][:-1].T) * acts[k] * (1 - acts[k])
                self.m[k] = 0.9 * self.m[k] + 0.1 * gW
                self.v[k] = 0.999 * self.v[k] + 0.001 * gW * gW
                mh = self.m[k] / (1 - 0.9 ** self.t); vh = self.v[k] / (1 - 0.999 ** self.t)
                self.W[k] -= self.lr * mh / (np.sqrt(vh) + 1e-8)

    def fit_initial(self, X):
        self._train(X, self.ei)

    def update(self, X):
        self._train(X, self.eu)

    def reconstruct(self, X):
        return self._fwd(np.atleast_2d(X))[-1]


def ids_output(model, X):
    """Decision maker, eq. (5): mean absolute deviation, clipped to [0,1]."""
    return np.clip(np.mean(np.abs(np.atleast_2d(X) - model.reconstruct(X)), axis=1), 0, 1)
