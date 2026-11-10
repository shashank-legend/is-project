"""
Convert a Kitsune / Bot-IoT capture into the packet CSV used by run_experiments.py.

Kitsune (Mirai) ships `Mirai_pcap.pcap` and `Mirai_labels.csv` (one 0/1 label per
packet, same order). Export timestamps and lengths with tshark first:

    tshark -r Mirai_pcap.pcap -T fields -e frame.time_epoch -e frame.len -E separator=, > mirai_fields.csv
    python pcap_to_csv.py mirai_fields.csv Mirai_labels.csv kitsune_mirai_packets.csv
    python run_experiments.py --csv kitsune_mirai_packets.csv --seeds 3
"""
import sys
import numpy as np

fields, labels, out = sys.argv[1], sys.argv[2], sys.argv[3]
F = np.genfromtxt(fields, delimiter=",")
lab = np.genfromtxt(labels, delimiter=",", skip_header=1)
lab = lab[:, -1] if lab.ndim > 1 else lab
n = min(len(F), len(lab))
np.savetxt(out, np.column_stack([F[:n, 0], F[:n, 1], lab[:n]]), delimiter=",",
           header="timestamp,length,label", comments="", fmt=["%.6f", "%d", "%d"])
print(f"wrote {n} packets to {out}")
