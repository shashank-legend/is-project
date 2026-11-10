"""
Reproduces the experiments of the report.

    python run_experiments.py               # full run (5 seeds, ~10-15 min on a laptop)
    python run_experiments.py --quick       # 1 seed, smoke test
    python run_experiments.py --csv kitsune_mirai_packets.csv   # real data (see README)

Outputs go to results/: summary tables (CSV + Markdown), per-run CSV, figures.
"""
import argparse, json, os, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score, roc_curve

from ssid import (make_scenario, load_packet_csv, extract_metrics, AADRNN, AEMLP,
                  SSID, run_offline, run_incremental, smooth, ids_output)

GAMMA, I_WIN = 0.25, 10
WARMUP = 500           # packets needed to fill the 500-packet metric window
N_OFFLINE = 5000       # oracle-labelled benign packets for offline baselines
PLUS = dict(unbiased_kappa=True, rep="js", gate=True, adaptive_gamma=True)
COLORS = {"SSID+ (ours)": "#0F766E", "SSID-AADRNN (paper)": "#B45309", "SSID-MLP (paper)": "#D97706",
          "Offline-AADRNN": "#475569", "Incremental-AADRNN": "#94A3B8", "Offline-KNN": "#7C3AED",
          "Offline-IForest": "#A78BFA"}


def prepare(stream):
    X, tt, pl = extract_metrics(stream)
    t, L = stream.t[WARMUP:], stream.label[WARMUP:]
    ev = stream.events or {}
    P1 = t < ev.get("drift", np.inf)
    P2 = (t >= ev.get("drift", np.inf)) & (t < ev.get("attack", np.inf))
    return X[WARMUP:], tt[WARMUP:], pl[WARMUP:], t, L, P1, P2


def score(pred, s, L, P1, P2):
    ben = (L == 0) & (P1 | P2)          # benign packets not contaminated by attack windows
    att = L == 1
    if not ben.any():                   # real CSV without phase info
        ben = L == 0
    tpr, fpr = pred[att].mean(), pred[ben].mean()
    out = dict(TPR=tpr, TNR=1 - fpr, BalAcc=0.5 * (tpr + 1 - fpr),
               FPR_P1=pred[P1 & (L == 0)].mean() if (P1 & (L == 0)).any() else np.nan,
               FPR_P2=pred[P2 & (L == 0)].mean() if (P2 & (L == 0)).any() else np.nan)
    m = ben | att
    out["AUC"] = roc_auc_score(L[m], s[m]) if len(np.unique(L[m])) == 2 else np.nan
    return out


def offline_sklearn(kind, X, tr):
    Xtr = X[tr]
    if kind == "knn":
        nn = NearestNeighbors(n_neighbors=5).fit(Xtr[::2])
        sc = nn.kneighbors(X)[0].mean(1); ref = nn.kneighbors(Xtr[1::2])[0].mean(1)
    else:
        f = IsolationForest(n_estimators=100, random_state=0).fit(Xtr)
        sc = -f.score_samples(X); ref = -f.score_samples(Xtr)
    thr = np.quantile(ref, 0.995)
    s = smooth(sc, I_WIN)
    return s > thr, s


def run_all(X, tt, pl, L, seed, which):
    res, traces = {}, {}
    ben_idx = np.where(L == 0)[0][:N_OFFLINE]
    for name in which:
        t0 = time.perf_counter(); extra = {}
        if name == "Offline-AADRNN":
            y = run_offline(AADRNN(seed=seed), X, ben_idx); s = smooth(y, I_WIN); pred = s > GAMMA
        elif name == "Incremental-AADRNN":
            y = run_incremental(AADRNN(seed=seed), X, 750, GAMMA, I_WIN); s = smooth(y, I_WIN); pred = s > GAMMA
        elif name in ("Offline-KNN", "Offline-IForest"):
            pred, s = offline_sklearn("knn" if "KNN" in name else "if", X, ben_idx)
        else:
            if name == "SSID-AADRNN (paper)":
                f = SSID(AADRNN(seed=seed), seed=seed)
            elif name == "SSID-MLP (paper)":
                f = SSID(AEMLP(seed=seed), seed=seed)
            elif name == "SSID+ (ours)":
                f = SSID(AADRNN(seed=seed, forget=0.995), seed=seed, **PLUS)
            else:                                    # ablation "SSID +<flag>"
                flag = name.split("+")[1].strip()
                kw = {"gate": dict(gate=True), "adaptive-gamma": dict(adaptive_gamma=True),
                      "JS-rep": dict(rep="js"), "unbiased-kappa": dict(unbiased_kappa=True),
                      "forgetting": {}}[flag]
                f = SSID(AADRNN(seed=seed, forget=0.995 if flag == "forgetting" else 1.0), seed=seed, **kw)
            y, s, G, rec = f.run(X, tt, pl)
            pred = s > rec["thr"]
            extra = dict(learned=f.n_learned, updates=f.n_updates, phases=f.phases)
            traces[name] = dict(s=s, G=G, thr=rec["thr"])
        extra["us_per_pkt"] = 1e6 * (time.perf_counter() - t0) / len(X)
        res[name] = (pred, s, extra)
    return res, traces


def fmt_table(rows, cols):
    head = "| Method | " + " | ".join(cols) + " |\n|---|" + "---|" * len(cols) + "\n"
    body = ""
    for name, r in rows.items():
        body += f"| {name} | " + " | ".join(r[c] for c in cols) + " |\n"
    return head + body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--csv", default=None)
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    os.makedirs(f"{a.out}/figures", exist_ok=True)
    seeds = [0] if a.quick else list(range(a.seeds))
    methods = ["Offline-AADRNN", "Incremental-AADRNN", "Offline-KNN", "Offline-IForest",
               "SSID-AADRNN (paper)", "SSID-MLP (paper)", "SSID+ (ours)"]
    ablations = ["SSID-AADRNN (paper)", "SSID + gate", "SSID + adaptive-gamma", "SSID + JS-rep",
                 "SSID + unbiased-kappa", "SSID + forgetting", "SSID+ (ours)"]
    scenarios = ["csv"] if a.csv else ["mirai", "mirai_drift", "slow_ramp"]

    per_run, keep = [], {}
    for sc in scenarios:
        for seed in seeds:
            st = load_packet_csv(a.csv, "csv") if a.csv else make_scenario(sc, seed)
            X, tt, pl, t, L, P1, P2 = prepare(st)
            which = methods + ([m for m in ablations if m not in methods] if sc == "slow_ramp" else [])
            res, traces = run_all(X, tt, pl, L, seed, which)
            for name, (pred, s, extra) in res.items():
                r = score(pred, s, L, P1, P2); r.update(extra); r.update(scenario=sc, seed=seed, method=name)
                per_run.append(r)
                print(f"{sc:12s} seed={seed} {name:24s} TPR={r['TPR']:.4f} TNR={r['TNR']:.4f} "
                      f"AUC={r['AUC']:.4f} {r['us_per_pkt']:.1f}us/pkt", flush=True)
            if seed == 0:
                keep[sc] = dict(t=t, L=L, traces=traces, ev=st.events,
                                roc={n: (L, res[n][1]) for n in res})

    # ---------------------------------------------------------------- tables
    import csv
    keys = ["scenario", "method", "seed", "TPR", "TNR", "BalAcc", "AUC", "FPR_P1", "FPR_P2",
            "learned", "updates", "phases", "us_per_pkt"]
    with open(f"{a.out}/per_run.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, keys); w.writeheader()
        for r in per_run:
            w.writerow({k: r.get(k, "") for k in keys})
    summary, md = {}, ""
    for sc in scenarios:
        rows = {}
        names = list(dict.fromkeys(r["method"] for r in per_run if r["scenario"] == sc))
        for n in names:
            rs = [r for r in per_run if r["scenario"] == sc and r["method"] == n]
            agg = {}
            for k in ["TPR", "TNR", "BalAcc", "AUC", "FPR_P2", "us_per_pkt", "learned"]:
                v = np.array([r.get(k, np.nan) for r in rs], float)
                agg[k] = (float(np.nanmean(v)) if np.isfinite(v).any() else np.nan,
                          float(np.nanstd(v)) if np.isfinite(v).any() else np.nan)
            summary.setdefault(sc, {})[n] = agg
            rows[n] = {k: ("-" if np.isnan(m) else (f"{m:.0f}" if k in ("learned",) else
                           f"{m:.1f}" if k == "us_per_pkt" else f"{m:.4f} ± {sd:.4f}"))
                       for k, (m, sd) in agg.items()}
        md += f"\n### Scenario: {sc}  (mean ± std over {len(seeds)} seed(s))\n\n" + \
              fmt_table(rows, ["TPR", "TNR", "BalAcc", "AUC", "FPR_P2", "learned", "us_per_pkt"])
    open(f"{a.out}/summary.md", "w").write(md)
    json.dump(summary, open(f"{a.out}/summary.json", "w"), indent=1)
    print(md)

    # ---------------------------------------------------------------- figures
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    for sc, k in keep.items():
        tr = k["traces"]
        if "SSID-AADRNN (paper)" not in tr:
            continue
        fig, ax = plt.subplots(2, 1, figsize=(9, 5.2), sharex=True)
        for j, n in enumerate(["SSID-AADRNN (paper)", "SSID+ (ours)"]):
            a_ = ax[j]; tt_ = k["t"]; step = 20
            a_.plot(tt_[::step], tr[n]["s"][::step], lw=0.7, color=COLORS[n], label="IDS output (avg of I=10)")
            a_.plot(tt_[::step], tr[n]["G"][::step], lw=1.4, color="#111827", label="trust coefficient Γ")
            a_.plot(tt_[::step], tr[n]["thr"][::step], lw=1, ls="--", color="#DC2626", label="intrusion threshold")
            a_.fill_between(tt_[::step], 0, 1, where=k["L"][::step] == 1, color="#FCA5A5", alpha=0.25, lw=0,
                            label="attack packets present")
            for lab, e in (k["ev"] or {}).items():
                a_.axvline(e, color="#6B7280", lw=0.8, ls=":")
                if j == 1:
                    a_.text(e + 15, 0.93, lab, fontsize=8, color="#6B7280")
            a_.set_ylim(0, 1.02); a_.set_title(n, loc="left", fontsize=10)
        ax[0].legend(loc="upper left", fontsize=8, ncol=2, frameon=False)
        ax[1].set_xlabel("time (s)")
        fig.tight_layout(); fig.savefig(f"{a.out}/figures/timeline_{sc}.png", dpi=170); plt.close(fig)

    if "mirai" in keep:                      # ROC, log-x like Fig. 4 of the paper
        fig, ax = plt.subplots(figsize=(5.2, 4))
        k = keep["mirai"]; ben = (k["L"] == 0) & (k["t"] < k["ev"]["attack"]); att = k["L"] == 1; m = ben | att
        for n in ["SSID+ (ours)", "SSID-AADRNN (paper)", "SSID-MLP (paper)", "Offline-AADRNN", "Offline-KNN"]:
            Lr, s = k["roc"][n]
            fpr, tpr, _ = roc_curve(Lr[m], s[m])
            ax.plot(np.maximum(fpr, 1e-6), tpr, label=n, color=COLORS[n], lw=1.5)
        ax.set_xscale("log"); ax.set_xlabel("FPR (log)"); ax.set_ylabel("TPR"); ax.set_ylim(0.5, 1.01)
        ax.legend(fontsize=7.5, frameon=False, loc="lower right"); ax.set_title("ROC – mirai scenario", fontsize=10)
        fig.tight_layout(); fig.savefig(f"{a.out}/figures/roc_mirai.png", dpi=170); plt.close(fig)

    fig, axes = plt.subplots(1, len(summary), figsize=(4.2 * len(summary), 3.8), sharey=True)
    axes = np.atleast_1d(axes)
    for a_, (sc, d) in zip(axes, summary.items()):
        names = [n for n in methods if n in d]
        v = [d[n]["BalAcc"][0] for n in names]; e = [d[n]["BalAcc"][1] for n in names]
        a_.barh(range(len(names)), v, xerr=e, color=[COLORS[n] for n in names], height=0.65)
        a_.set_yticks(range(len(names))); a_.set_yticklabels(names, fontsize=8)
        for i, x in enumerate(v):
            a_.text(min(x, 0.98) - 0.01, i, f"{x:.3f}", va="center", ha="right", color="white", fontsize=7.5)
        a_.set_xlim(0.4, 1.0); a_.set_title(sc, fontsize=10); a_.set_xlabel("balanced accuracy")
        a_.invert_yaxis()
    fig.tight_layout(); fig.savefig(f"{a.out}/figures/balacc_comparison.png", dpi=170); plt.close(fig)

    if "slow_ramp" in summary:
        d = summary["slow_ramp"]; names = [n for n in ablations if n in d]
        fig, ax = plt.subplots(figsize=(7, 3.4))
        v = [d[n]["TPR"][0] for n in names]
        ax.bar(range(len(names)), v, color=["#B45309"] + ["#94A3B8"] * (len(names) - 2) + ["#0F766E"])
        ax.set_xticks(range(len(names))); ax.set_xticklabels([n.replace("SSID + ", "+") for n in names], rotation=20, fontsize=8)
        for i, x in enumerate(v):
            ax.text(i, x + 0.02, f"{x:.2f}", ha="center", fontsize=8)
        ax.set_ylabel("TPR (slow-ramp attack)"); ax.set_ylim(0, 1.1)
        ax.set_title("Ablation: which SSID+ component stops self-poisoning", fontsize=10)
        fig.tight_layout(); fig.savefig(f"{a.out}/figures/ablation_slow_ramp.png", dpi=170); plt.close(fig)

    # hyper-parameter sensitivity of the paper's SSID (theta x gamma)
    if not a.csv:
        thetas, gammas = [0.90, 0.95, 0.98], [0.10, 0.25, 0.40]
        H = np.zeros((len(thetas), len(gammas)))
        sens_seeds = seeds[:3]
        for i, th in enumerate(thetas):
            for j, g in enumerate(gammas):
                vals = []
                for seed in sens_seeds:
                    st = make_scenario("mirai_drift", seed); X, tt, pl, t, L, P1, P2 = prepare(st)
                    f = SSID(AADRNN(seed=seed), theta=th, gamma=g, seed=seed)
                    y, s, G, rec = f.run(X, tt, pl)
                    vals.append(score(s > rec["thr"], s, L, P1, P2)["BalAcc"])
                H[i, j] = np.mean(vals)
                print(f"sensitivity theta={th} gamma={g} BalAcc={H[i, j]:.4f}", flush=True)
        np.savetxt(f"{a.out}/sensitivity_theta_gamma.csv", H, delimiter=",", fmt="%.4f")
        fig, ax = plt.subplots(figsize=(4.4, 3.6))
        im = ax.imshow(H, cmap="YlGnBu", vmin=0.5, vmax=1)
        ax.set_xticks(range(3)); ax.set_xticklabels(gammas); ax.set_yticks(range(3)); ax.set_yticklabels(thetas)
        ax.set_xlabel("intrusion threshold γ"); ax.set_ylabel("trust threshold Θ")
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{H[i, j]:.3f}", ha="center", va="center", fontsize=9,
                        color="white" if H[i, j] > 0.8 else "black")
        ax.set_title("Paper SSID: balanced accuracy\n(mirai_drift, mean of 3 seeds)", fontsize=9.5)
        fig.colorbar(im, fraction=0.046); fig.tight_layout()
        fig.savefig(f"{a.out}/figures/sensitivity_theta_gamma.png", dpi=170); plt.close(fig)


if __name__ == "__main__":
    main()
