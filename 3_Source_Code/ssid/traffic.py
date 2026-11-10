"""
Packet-stream generation and traffic-metric extraction.

The paper evaluates on the Kitsune (Mirai) and Bot-IoT datasets. Those datasets
need a Kaggle / UNSW login and several GB of pcap, so this module provides:

  1. A reproducible synthetic IoT packet-stream generator with the phenomena the
     paper cares about (benign drift when new devices join, a Mirai-like
     scanning/flooding botnet attack) plus a "slow-ramp" attack that the paper
     does NOT evaluate and that we use to probe self-poisoning.
  2. A loader for a real packet CSV (timestamp, length, label) so the same code can
     be run on Kitsune/Bot-IoT once the user exports packets with tshark
     (see README.md).

Metric extraction follows Section III-B-1 of Nakip & Gelenbe (2024):
  M = 3 metrics per packet for malicious-traffic detection:
    m1: total size of the last 500 packets
    m2: average inter-transmission time of the last 500 packets
    m3: number of packets in the last 100 seconds
All metrics are causal (use only packets up to and including i).
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class PacketStream:
    t: np.ndarray        # timestamps (s), sorted
    length: np.ndarray   # packet length (bytes)
    label: np.ndarray    # 0 = benign, 1 = malicious (used ONLY for evaluation)
    name: str = "stream"
    events: dict = None  # e.g. {"drift": 1200.0, "attack": 2400.0}


def _benign_device_packets(rng, t0, t1, rate, mean_len, small_frac=0.55):
    """Poisson arrivals; bimodal packet lengths (control vs data packets)."""
    n = rng.poisson(rate * (t1 - t0))
    t = np.sort(rng.uniform(t0, t1, n))
    small = rng.random(n) < small_frac
    L = np.where(small,
                 rng.normal(66, 6, n),                    # ACK / control packets
                 rng.exponential(mean_len, n) + 90)       # data packets
    return t, np.clip(L, 54, 1514)


def make_scenario(kind="mirai_drift", seed=0, duration=3000.0):
    """
    Three phases: P1 = [0, T/3) stationary benign, P2 = [T/3, 2T/3) benign,
    P3 = [2T/3, T) attack (+ benign background).
    kind:
      'mirai'       : stationary benign traffic, then an abrupt Mirai-like
                      flood (high-rate small scan/SYN packets). Closest to the
                      paper's Kitsune-Mirai setting.
      'mirai_drift' : as 'mirai', but during P2 four new devices join one by
                      one (every 200 s) - benign concept drift, the situation
                      that motivates SSID.
      'slow_ramp'   : drift as above, but the attack rate ramps up linearly
                      from 0 over 900 s ("boiling-frog") - a stress test for
                      self-labelling / self-poisoning that the paper does not run.
    """
    rng = np.random.default_rng(seed)
    T_drift, T_att = duration / 3, 2 * duration / 3
    ts, Ls, ys = [], [], []

    for _ in range(6):                                   # original devices
        t, L = _benign_device_packets(rng, 0, duration, rng.uniform(0.6, 1.6), rng.uniform(150, 450))
        ts.append(t); Ls.append(L); ys.append(np.zeros_like(t))
    if kind in ("mirai_drift", "slow_ramp"):             # devices join gradually
        for k in range(4):
            t0 = T_drift + 200.0 * k
            t, L = _benign_device_packets(rng, t0, duration, rng.uniform(0.8, 1.6), rng.uniform(500, 900), 0.35)
            ts.append(t); Ls.append(L); ys.append(np.zeros_like(t))

    rmax = 60.0
    if kind in ("mirai", "mirai_drift"):
        n = rng.poisson(rmax * (duration - T_att))
        t = np.sort(rng.uniform(T_att, duration, n))
    elif kind == "slow_ramp":
        ramp = 900.0
        n = rng.poisson(rmax * (duration - T_att))
        cand = np.sort(rng.uniform(T_att, duration, n))
        keep = rng.random(n) < np.minimum(1.0, (cand - T_att) / ramp)   # thinning
        t = cand[keep]
    else:
        raise ValueError(kind)
    L = np.clip(rng.normal(60, 4, len(t)), 54, 80)       # tiny scan / SYN packets
    ts.append(t); Ls.append(L); ys.append(np.ones_like(t))

    t = np.concatenate(ts); L = np.concatenate(Ls); y = np.concatenate(ys)
    o = np.argsort(t, kind="stable")
    return PacketStream(t[o], L[o], y[o].astype(int), kind, {"drift": T_drift, "attack": T_att})


def load_packet_csv(path, name="csv"):
    """CSV with header: timestamp,length,label  (label 0/1)."""
    d = np.genfromtxt(path, delimiter=",", names=True)
    o = np.argsort(d["timestamp"], kind="stable")
    return PacketStream(d["timestamp"][o], d["length"][o], d["label"][o].astype(int), name, {})


# Normalisation constants (log-scaling into [0,1]); fixed a-priori so that the
# pipeline needs no offline data, in the spirit of SSID.
# log10 ranges: total size of 500 pkts, mean inter-transmission time, count/100 s
NORM = {"size": (4.3, 5.8), "itt": (-2.5, 0.5), "count": (1.5, 4.0)}


def _lg(v, rng):
    lo, hi = rng
    return (np.log10(np.maximum(v, 1e-9)) - lo) / (hi - lo)


def extract_metrics(s: PacketStream, win_pk=500, win_s=100.0):
    t, L = s.t, s.length
    n = len(t)
    cs = np.concatenate([[0.0], np.cumsum(L)])
    idx = np.arange(n)
    lo = np.maximum(0, idx - win_pk + 1)
    total = cs[idx + 1] - cs[lo]                                   # m1
    span = np.maximum(idx - lo, 1)
    itt = (t - t[lo]) / span                                       # m2
    count = idx - np.searchsorted(t, t - win_s, side="left") + 1   # m3
    X = np.stack([
        _lg(total, NORM["size"]),
        _lg(itt, NORM["itt"]),
        _lg(count, NORM["count"]),
    ], axis=1)
    # raw per-packet properties used by the representativeness factor (TT, PL)
    tt = np.diff(t, prepend=t[0])
    if n > 1:
        tt[0] = tt[1]
    return np.clip(X, 0, 1), tt, L.astype(float)
