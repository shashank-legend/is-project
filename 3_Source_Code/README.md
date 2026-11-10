# SSID / SSID+ — implementation and experimental validation

This is a re-implementation of the paper below, together with our improved variant, **SSID+**:

> M. Nakıp and E. Gelenbe, "Online Self-Supervised Deep Learning for Intrusion Detection Systems," *IEEE TIFS*, vol. 19, pp. 5668–5683, 2024.

## Layout

| Path | Content |
|---|---|
| `ssid/traffic.py` | Synthetic IoT scenarios (`mirai`, `mirai_drift`, `slow_ramp`), a packet-CSV loader, and causal extraction of the M = 3 traffic metrics |
| `ssid/models.py` | DRNN activation ζ (eq. 4), FISTA (eq. 7), AADRNN with OS-ELM (eqs. 10–12) plus a forgetting factor, and an MLP auto-encoder (Adam) |
| `ssid/framework.py` | The SSID controller (eqs. 13–38) with SSID+ switches (`rep="js"`, `unbiased_kappa`, `gate`, `adaptive_gamma`), and the offline and incremental baselines |
| `run_experiments.py` | Every scenario × seed × method, the ablation, the Θ×γ sensitivity grid, tables and figures |
| `make_diagrams.py` | The architecture figures used in the report and slides |
| `pcap_to_csv.py` | Converts the real Kitsune / Bot-IoT captures into the CSV format |
| `results/` | Output of the full run: `summary.md`, `summary.json`, `per_run.csv`, `sensitivity_theta_gamma.csv`, `figures/` |

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python make_diagrams.py
python run_experiments.py --quick      # 1 seed, ~3 min
python run_experiments.py              # 5 seeds + ablation + sensitivity, ~15 min
```

Tested with Python 3.9, NumPy 2.0, scikit-learn 1.6 and Matplotlib 3.9.

### Running on real Kitsune-Mirai data

```bash
tshark -r Mirai_pcap.pcap -T fields -e frame.time_epoch -e frame.len -E separator=, > mirai_fields.csv
python pcap_to_csv.py mirai_fields.csv Mirai_labels.csv kitsune_mirai.csv
python run_experiments.py --csv kitsune_mirai.csv --seeds 3 --out results_kitsune
```

The metric normalisation ranges (`NORM` in `ssid/traffic.py`) and γ may need re-checking for real traffic. The report covers this in §6.2 and §8.7.

## Headline results (5 seeds, mean)

| Scenario | SSID-AADRNN (paper) BalAcc | SSID+ (ours) BalAcc | SSID TPR → SSID+ TPR |
|---|---|---|---|
| mirai | 0.995 | 0.997 | 0.990 → 0.995 |
| mirai_drift | 0.984 | 0.998 | 0.969 → 0.996 |
| slow_ramp | 0.501 | 0.992 | **0.002 → 0.985** |

The full tables are in `results/summary.md`.

## Implementation choices not specified in the paper

- A ridge term of 1e-3 when initialising O₀. It is singular with fewer than M+1 samples.
- Frozen min-max input scaling for the hidden layers. Without it, the non-negative L1 problem (7) collapses onto the bias row.
- The last hidden layer is standardised before the linear output layer.
- The untrained model outputs y = 0.5. With y = 1 the bootstrap deadlocks.
- During l = 0, all packets count as "observed" traffic for C_rep.
- During l = 0, the hidden layers are refitted at |B₀| = 2^k and every 100 packets. OS-ELM updates run in between.
- The batch B is capped at 5,000 packets.
- The first 500 packets are skipped while the metric window fills.
