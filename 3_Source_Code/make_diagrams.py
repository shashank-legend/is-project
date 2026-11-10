"""Draws the system diagrams used in the report and slides (team's own
re-drawings of Figs. 1-3 of Nakip & Gelenbe, 2024, plus the SSID+ additions)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

os.makedirs("results/figures", exist_ok=True)
INK, MUTED = "#111827", "#6B7280"
TEAL, AMBER, SLATE, RED = "#0F766E", "#B45309", "#334155", "#B91C1C"


def box(ax, x, y, w, h, text, fc="#F1F5F9", ec=SLATE, fs=8.5, color=INK, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=color,
            weight="bold" if bold else "normal", wrap=True)


def arrow(ax, p, q, color=SLATE, ls="-", text=None, off=(0, 0.12)):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=11, color=color, lw=1.2, ls=ls))
    if text:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, ha="center",
                fontsize=7.5, color=color)


# ---------------------------------------------------------------- SSID overview
fig, ax = plt.subplots(figsize=(11, 5.2)); ax.set_xlim(0, 11); ax.set_ylim(0, 5.4); ax.axis("off")
ax.text(0.1, 5.15, "Detection line (unchanged IDS)", fontsize=9.5, color=SLATE, weight="bold")
box(ax, 0.1, 3.75, 1.5, 1.0, "Packet stream\n(header only)")
box(ax, 2.0, 3.75, 1.8, 1.0, "Traffic metrics\nx_i ∈ [0,1]^M\n(M = 3)")
box(ax, 4.2, 3.75, 2.0, 1.0, "AADRNN\nauto-associative\nmemory  x̂_i = f(x_i)")
box(ax, 6.6, 3.75, 1.9, 1.0, "Decision maker\ny_i = mean|x_i − x̂_i|")
box(ax, 8.9, 3.75, 1.9, 1.0, "Alarm if\nmean(y over I=10) > γ", fc="#FEE2E2", ec=RED)
for a_, b_ in [((1.6, 4.25), (2.0, 4.25)), ((3.8, 4.25), (4.2, 4.25)), ((6.2, 4.25), (6.6, 4.25)),
               ((8.5, 4.25), (8.9, 4.25))]:
    arrow(ax, a_, b_)

ax.text(0.1, 3.1, "Learning line (SSID, runs in parallel)", fontsize=9.5, color=AMBER, weight="bold")
box(ax, 0.1, 1.55, 2.3, 1.25, "Self-supervised\npacket selection\np⁻ = Γ(1−y),  p⁺ = Γy\nq = 1 − Γ", fc="#FEF3C7", ec=AMBER)
box(ax, 2.8, 1.55, 2.3, 1.25, "Trust coefficient\nΓ = C_rep · C_gen", fc="#FEF3C7", ec=AMBER, bold=True)
box(ax, 2.8, 0.1, 1.1, 1.15, "C_rep\nKL of TT, PL\n(exponential)", fc="#FFFBEB", ec=AMBER, fs=7.5)
box(ax, 4.0, 0.1, 1.1, 1.15, "C_gen\n½Δ + ½κ\n(data, knowl.)", fc="#FFFBEB", ec=AMBER, fs=7.5)
box(ax, 5.5, 1.55, 2.5, 1.25, "Phase control\nl=0: update every selected pkt\nuntil Γ ≥ Θ\nl≥1: update if Γ<Θ, |B|≥K,\nno alarm; alarm → empty B", fc="#FEF3C7", ec=AMBER, fs=7.8)
box(ax, 8.4, 1.55, 2.4, 1.25, "Parameter update\nl=0: FISTA (hidden) + LS\nl≥1: OS-ELM on output layer", fc="#FEF3C7", ec=AMBER, fs=7.8)
arrow(ax, (7.55, 3.75), (1.25, 2.8), color=AMBER, ls="--", text="y_i (IDS's own decision)", off=(0, 0.25))
arrow(ax, (3.95, 1.55), (3.35, 1.25), color=AMBER); arrow(ax, (3.95, 1.55), (4.55, 1.25), color=AMBER)
arrow(ax, (2.8, 2.17), (2.4, 2.17), color=AMBER)
ax.plot([1.25, 1.25, 6.75], [1.55, 1.40, 1.40], color=AMBER, lw=1.2)
arrow(ax, (6.75, 1.40), (6.75, 1.55), color=AMBER)
ax.text(6.0, 1.45, "batch B_l", fontsize=7.5, color=AMBER, ha="center")
arrow(ax, (8.0, 2.17), (8.4, 2.17), color=AMBER)
arrow(ax, (9.6, 2.8), (5.2, 3.75), color=AMBER, text="new weights", off=(0.4, 0.05))
arrow(ax, (9.6, 1.55), (5.1, 1.0), color=AMBER, ls=":", text="E(l), Σ|B_k|", off=(1.2, -0.05))
ax.text(5.6, 0.38, "SSID+ (ours) replaces / adds:\n• C_rep → sliding-window Jensen–Shannon (distribution-free)\n"
        "• κ → bias-corrected EWMA   • confidence gate on p⁻\n• adaptive γ_t = μ + kσ   • forgetting-factor OS-ELM",
        fontsize=7.8, color=TEAL, va="center",
        bbox=dict(boxstyle="round,pad=0.4", fc="#ECFDF5", ec=TEAL))
fig.tight_layout(); fig.savefig("results/figures/ssid_architecture.png", dpi=180); plt.close(fig)

# ---------------------------------------------------------------- AADRNN
fig, ax = plt.subplots(figsize=(8, 3.2)); ax.set_xlim(0, 8); ax.set_ylim(0, 3.2); ax.axis("off")
xs = [0.6, 2.4, 4.2, 6.0]
labels = ["input x_i\n(M=3 metrics)", "hidden layer 1\nM dense clusters ζ(·)", "hidden layer 2\nM dense clusters ζ(·)", "output x̂_i\nM linear neurons"]
for k, x in enumerate(xs):
    for j in range(3):
        c = plt.Circle((x, 0.9 + 0.65 * j), 0.2, fc=["#E2E8F0", "#FEF3C7", "#FEF3C7", "#CCFBF1"][k], ec=SLATE)
        ax.add_patch(c)
    ax.text(x, 0.25, labels[k], ha="center", va="center", fontsize=7.8)
    if k < 3:
        for j in range(3):
            for jj in range(3):
                ax.plot([x + 0.2, xs[k + 1] - 0.2], [0.9 + 0.65 * j, 0.9 + 0.65 * jj], color="#CBD5E1", lw=0.6)
        ax.text((x + xs[k + 1]) / 2, 2.95, ["W₁ (FISTA, eq.7)", "W₂ (FISTA, eq.7)", "W_H (OS-ELM, eq.10-12)"][k],
                ha="center", fontsize=8, color=AMBER if k < 2 else TEAL)
box(ax, 6.65, 1.25, 1.3, 0.9, "y_i = mean\n|x − x̂|", fc="#FEE2E2", ec=RED, fs=8)
fig.tight_layout(); fig.savefig("results/figures/aadrnn.png", dpi=180); plt.close(fig)
print("diagrams written")
