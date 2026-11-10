import json, sys, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, Table,
                                TableStyle, PageBreak, KeepTogether, Preformatted)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = sys.argv[1]
OUT = sys.argv[2]
FIG = os.path.join(ROOT, "3_Source_Code/results/figures")
S = json.load(open(os.path.join(ROOT, "3_Source_Code/results/summary.json")))
SENS = [[float(v) for v in l.split(",")] for l in open(os.path.join(ROOT, "3_Source_Code/results/sensitivity_theta_gamma.csv"))]

# Unicode font (Greek letters, math symbols)
for name, f in [("DV", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf")]:
    pdfmetrics.registerFont(TTFont(name, f))
BODY = "DV"

TEAL = colors.HexColor("#0F766E"); AMBER = colors.HexColor("#B45309"); INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#4B5563"); LIGHT = colors.HexColor("#F1F5F9")

ss = getSampleStyleSheet()
st = {
    "body": ParagraphStyle("body", fontName=BODY, fontSize=10, leading=14.2, alignment=TA_JUSTIFY, spaceAfter=6, textColor=INK),
    "h1": ParagraphStyle("h1", keepWithNext=1, fontName=BODY, fontSize=16, leading=20, spaceBefore=10, spaceAfter=8, textColor=INK),
    "h2": ParagraphStyle("h2", keepWithNext=1, fontName=BODY, fontSize=12.5, leading=16, spaceBefore=8, spaceAfter=5, textColor=INK),
    "h3": ParagraphStyle("h3", keepWithNext=1, fontName=BODY, fontSize=10.5, leading=14, spaceBefore=5, spaceAfter=3, textColor=TEAL),
    "cap": ParagraphStyle("cap", fontName=BODY, fontSize=8.6, leading=11, textColor=MUTED, alignment=TA_CENTER, spaceAfter=10),
    "eq": ParagraphStyle("eq", fontName=BODY, fontSize=10, leading=15, alignment=TA_CENTER, spaceBefore=2, spaceAfter=6),
    "bul": ParagraphStyle("bul", fontName=BODY, fontSize=10, leading=14, leftIndent=14, bulletIndent=4, spaceAfter=3, alignment=TA_JUSTIFY),
    "cell": ParagraphStyle("cell", fontName=BODY, fontSize=8.4, leading=10.5),
    "cellb": ParagraphStyle("cellb", fontName=BODY, fontSize=8.4, leading=10.5, textColor=colors.white),
    "tag_a": ParagraphStyle("taga", fontName=BODY, fontSize=8, leading=10, textColor=AMBER, spaceAfter=4),
    "tag_t": ParagraphStyle("tagt", fontName=BODY, fontSize=8, leading=10, textColor=TEAL, spaceAfter=4),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=7.8, leading=9.6, backColor=LIGHT, leftIndent=6, borderPadding=6),
    "title": ParagraphStyle("title", fontName=BODY, fontSize=22, leading=28, alignment=TA_CENTER, textColor=INK),
    "sub": ParagraphStyle("sub", fontName=BODY, fontSize=12, leading=17, alignment=TA_CENTER, textColor=MUTED),
}
P = lambda t, s="body": Paragraph(t, st[s])
AUTH = lambda: P("■ ORIGINAL AUTHORS' CONTRIBUTION — summarised from Nakıp &amp; Gelenbe [1]", "tag_a")
TEAM = lambda: P("■ TEAM'S OWN ANALYSIS / CONTRIBUTION", "tag_t")


def bullets(items):
    return [Paragraph(i, st["bul"], bulletText="•") for i in items]


def table(rows, widths, header=True, zebra=True):
    data = [[Paragraph(str(c), st["cellb" if (header and r == 0) else "cell"]) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    sty = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        sty.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")))
    if zebra:
        for r in range(1, len(rows)):
            if r % 2 == 0:
                sty.append(("BACKGROUND", (0, r), (-1, r), LIGHT))
    t.setStyle(TableStyle(sty))
    return t


def fig(name, w, cap):
    from reportlab.lib.utils import ImageReader
    path = os.path.join(FIG, name)
    iw, ih = ImageReader(path).getSize()
    return KeepTogether([Image(path, width=w, height=w * ih / iw), P(cap, "cap")])


class Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=2.1 * cm, rightMargin=2.1 * cm, topMargin=2 * cm, bottomMargin=2 * cm, **kw)
        fr = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate("p", [fr], onPage=self._deco)])

    def _deco(self, c, d):
        if d.page == 1:
            return
        c.saveState(); c.setFont(BODY, 8); c.setFillColor(MUTED)
        c.drawString(2.1 * cm, 1.2 * cm, "Research Paper Analysis — Online Self-Supervised Deep Learning for IDS (SSID)")
        c.drawRightString(A4[0] - 2.1 * cm, 1.2 * cm, str(d.page)); c.restoreState()

    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name in ("h1", "h2"):
            lvl = 0 if f.style.name == "h1" else 1
            key = "k%d" % id(f)
            self.canv.bookmarkPage(key)
            self.notify("TOCEntry", (lvl, f.getPlainText(), self.page, key))
            self.canv.addOutlineEntry(f.getPlainText(), key, level=lvl)


def m(sc, meth, k, nd=3):
    v = S[sc][meth][k][0]
    return f"{v:.{nd}f}"


def ms(sc, meth, k, nd=3):
    v, s = S[sc][meth][k]
    return f"{v:.{nd}f} ± {s:.{nd}f}"


W = A4[0] - 4.2 * cm
E = []
# ------------------------------------------------------------------ title page
E += [Spacer(1, 3.2 * cm), P("Research Paper Analysis", "sub"), Spacer(1, 6),
      P("Online Self-Supervised Deep Learning for Intrusion Detection Systems", "title"), Spacer(1, 10),
      P("Technical Documentation — critical analysis, proposed improvements (SSID+) and experimental validation", "sub"),
      Spacer(1, 1.2 * cm),
      P("Paper analysed: M. Nakıp and E. Gelenbe, “Online Self-Supervised Deep Learning for Intrusion Detection Systems,” "
        "<i>IEEE Transactions on Information Forensics and Security</i>, vol. 19, pp. 5668–5683, 2024. "
        "DOI: 10.1109/TIFS.2024.3402148", "sub"),
      Spacer(1, 1.4 * cm),
      table([["Team member", "Roll number", "Main responsibility"],
             ["&lt;Member 1&gt;", "&lt;roll no.&gt;", "Problem, motivation, related work (§1–2)"],
             ["&lt;Member 2&gt;", "&lt;roll no.&gt;", "System model, methodology, algorithms (§3–4)"],
             ["&lt;Member 3&gt;", "&lt;roll no.&gt;", "Evaluation of results, critical assessment (§5–6)"],
             ["&lt;Member 4&gt;", "&lt;roll no.&gt;", "Improvements SSID+, implementation, experiments (§7–8)"]],
            [4.5 * cm, 3.5 * cm, 8.8 * cm]),
      Spacer(1, 1 * cm),
      P("Course: Information Security — Research Paper Analysis Assignment", "sub"),
      P("Colour convention used throughout: <font color='#B45309'>■ amber tags</font> mark content summarised from the "
        "original authors; <font color='#0F766E'>■ teal tags</font> mark the team's own analysis, proposals and results.", "sub"),
      PageBreak()]

toc = TableOfContents()
toc.levelStyles = [ParagraphStyle("t0", fontName=BODY, fontSize=10, leading=13, leftIndent=0),
                   ParagraphStyle("t1", fontName=BODY, fontSize=9, leading=11.2, leftIndent=16, textColor=MUTED)]
E += [Paragraph("Contents", ParagraphStyle("hx", parent=st["h1"])), toc, PageBreak()]

# ------------------------------------------------------------------ summary
E += [P("Executive Summary", "h1"),
      P("Nakıp and Gelenbe propose <b>SSID</b>, a framework that trains a deep-learning anomaly-based intrusion detection "
        "system (IDS) <i>fully online</i>, with no offline dataset, no human labelling and no extra generative model. The IDS "
        "labels its own training data: every packet is selected as a benign training sample with probability Γ(1−y), where y is "
        "the IDS's estimated attack probability and Γ ∈ [0,1] is a <i>trust coefficient</i> that SSID computes online. Γ is the product of "
        "a <i>representativeness</i> factor (how well the traffic learned so far matches the traffic now being observed, measured with a "
        "closed-form KL divergence) and a <i>generalisation</i> factor (data adequacy plus a running estimate of the training error). Trust "
        "also decides <i>when</i> to retrain. The model updates only when Γ drops below Θ = 0.95 and no attack is in progress. "
        "With an Auto-Associative Deep Random Neural Network (AADRNN), the authors report TPR above 0.995 at an FPR of about 10⁻⁵ on Kitsune-Mirai "
        "after learning from only 4,161 packets, and gains of up to 18% median balanced accuracy for compromised-device identification on Bot-IoT."),
      P("Our analysis finds the idea sound and very lightweight, but we identify several weaknesses the paper does not discuss. "
        "(i) The self-labelling loop can be <b>poisoned</b> by an attack that ramps up slowly. "
        "(ii) The <b>bootstrap can deadlock</b> (Γ stays at 0 forever) if the untrained model's first output is 1. "
        "(iii) The knowledge term κ is <b>biased upward</b>, and eqs. (10), (28) and (38) contain typos. "
        "(iv) The exponential-traffic assumption and the <b>cumulative</b> representativeness measure react slowly to drift. "
        "(v) The evaluation has no variance over runs, no sensitivity analysis on the scale-dependent threshold γ, no comparison with "
        "the online KitNET detector, and no adversarial scenario."),
      P("We re-implemented SSID with AADRNN and MLP backbones in Python and propose <b>SSID+</b>, which makes five changes: a sliding-window "
        "Jensen–Shannon representativeness factor, a bias-corrected κ, confidence-gated pseudo-labelling, an adaptive intrusion threshold "
        "and a forgetting-factor OS-ELM. We ran three scenarios over 5 seeds. On an abrupt Mirai-like flood and on gradual benign drift, our SSID "
        f"reproduction matches the paper's qualitative claims (balanced accuracy {m('mirai','SSID-AADRNN (paper)','BalAcc')} and "
        f"{m('mirai_drift','SSID-AADRNN (paper)','BalAcc')}). Under a slow-ramp attack the paper's SSID learns the attack as normal "
        f"(TPR {m('slow_ramp','SSID-AADRNN (paper)','TPR')}), whereas SSID+ keeps detecting it "
        f"(TPR {m('slow_ramp','SSID+ (ours)','TPR')}) with the same false-positive rate."),
      PageBreak()]

# ------------------------------------------------------------------ 1
E += [P("1. Research Problem, Motivation and Objectives", "h1"), AUTH(),
      P("1.1 Problem", "h2"),
      P("Botnets such as Mirai compromise large numbers of cheap IoT devices and use them for Distributed Denial-of-Service (DDoS) "
        "attacks, data leakage and further spread of malware. The authors cite reports that 27.7% of global website traffic in 2021 came "
        "from malicious bots. Two tasks matter during an ongoing attack: <b>detecting malicious traffic</b>, which enables a reactive "
        "response, and <b>identifying compromised devices</b>, which enables preventive isolation."),
      P("1.2 Motivation and significance", "h2"),
      P("Anomaly-based IDSs learn a model of normal traffic, so they can detect zero-day attacks. Their decisions depend on that model, "
        "though, and normal IoT traffic changes over time (devices join or leave, usage patterns shift). A model that is not updated "
        "produces more and more false alarms. Online learning is the natural fix, but the paper identifies two obstacles:"),
      *bullets(["<b>No labelled data:</b> enough collected and labelled traffic is rarely available for each network the IDS protects, "
                "and human labelling is slow and error-prone.",
                "<b>When to update:</b> frequent updates waste the limited compute of IoT nodes for little gain, while infrequent updates "
                "leave the model stale. The right update interval depends on the IDS's current state and on the traffic itself."]),
      P("1.3 Objectives and claimed contributions", "h2"),
      *bullets(["A <b>fully online self-supervised framework (SSID)</b> that works with any IDS that has learnable parameters, needs no offline "
                "data collection or training, and needs no human intervention.",
                "A <b>trust coefficient</b> Γ = C<sub>rep</sub>·C<sub>gen</sub> that measures the trustworthiness of the IDS online.",
                "<b>Self-supervised packet selection</b> that labels training packets using only the IDS's own outputs, weighted by Γ.",
                "<b>Trust-triggered updates</b>: parameters change only when trust falls below a threshold and no attack is detected.",
                "Evaluation on <b>Kitsune</b> and <b>Bot-IoT</b> for two tasks, with AADRNN and MLP backbones, against offline, incremental and "
                "sequential learning and against KNN and Lasso."]),
      P("1.4 Challenges involved", "h2"),
      P("A system that labels its own training data has to avoid confirmation bias: a wrong decision becomes training data and makes the "
        "next wrong decision more likely. It also has to start from nothing (cold start), and it must run on devices with little memory "
        "and compute. These challenges guide our critical assessment in Section 6.")]

# ------------------------------------------------------------------ 2
E += [P("2. Existing Approaches (Related Work)", "h1"), AUTH(),
      P("The paper groups prior work into three families. <b>Botnet/DDoS detection</b> covers SVM, MLP, DT, NB, KNN and RF classifiers, "
        "feature selection (CorrAUC), BiLSTM, N-BaIoT deep autoencoders and KitNET. Most of these are trained offline and many are supervised. "
        "<b>Compromised-device identification</b> covers port-scan analysis, evidence theory, federated anomaly detection (DÏoT), "
        "wavelet analysis of resource usage, and mobility-based detection. <b>Self-supervised IDS</b> work is summarised in the table below."),
      table([["Work", "Self-supervision mechanism", "Needs offline data?", "Extra generative / contrastive model?", "Online?"],
             ["Song & Kim [9]", "Noised pseudo-normal data from LSTM; Inception-ResNet", "Yes", "Yes (LSTM generator)", "No"],
             ["Wang et al. [10]", "BYOL + transfer learning", "Yes (normal + attack)", "Yes (contrastive)", "No"],
             ["Zhang et al. [11]", "Bidirectional GAN + adversarial training", "Yes", "Yes (GAN)", "No"],
             ["Kye et al. [12]", "Hierarchical AE with self-supervised signals", "Yes (normal)", "No", "No"],
             ["Caville et al. [13]", "GNN (E-GraphSAGE) contrastive", "Yes", "Yes (contrastive)", "No"],
             ["Abououf et al. [15]", "LSTM-AE trained in the cloud", "Yes", "No", "Partly"],
             ["Meyer et al. [16]", "Federated AE self-supervision", "Yes (local)", "No", "No"],
             ["<b>SSID [1]</b>", "IDS's own decisions weighted by trust Γ", "<b>No</b>", "<b>No</b>", "<b>Yes</b>"]],
            [2.8 * cm, 5.0 * cm, 2.9 * cm, 3.3 * cm, 2.8 * cm]),
      P("Table 1 — Comparison of self-supervised IDS approaches (team's condensed re-statement of Table I in [1]).", "cap"),
      TEAM(),
      P("The table omits one relevant baseline: <b>KitNET/Kitsune</b> [17], which is itself an <i>online, unsupervised</i> ensemble of "
        "autoencoders, published together with the Kitsune dataset that this paper uses. KitNET also needs only a short benign "
        "\"grace period\" to start. That makes it the most natural competitor to SSID, yet it is not compared (see §6.4).")]

# ------------------------------------------------------------------ 3
E += [P("3. System Model and Architecture", "h1"), AUTH(),
      P("SSID wraps around an existing IDS. The <b>detection line</b> is left unchanged. A parallel <b>learning line</b> reads the IDS's "
        "decisions, decides how far it trusts them, selects and labels packets, and decides when to update parameters (Fig. 1)."),
      fig("ssid_architecture.png", W, "Figure 1 — SSID architecture (team's re-drawing of Figs. 2–3 of [1]). The teal box lists the changes in our SSID+ (§7)."),
      P("3.1 IDS used inside SSID: AADRNN", "h2"),
      P("The IDS is an auto-associative memory (AAM) f<sub>aam</sub>: [0,1]<super>M</super> → [0,1]<super>M</super> that maps observed "
        "traffic metrics x<sub>i</sub> to the metrics expected under benign traffic, x̂<sub>i</sub>. A large reconstruction deviation "
        "points to an attack. The AAM is a Deep Random Neural Network (DRNN) with H = M layers: M−1 hidden layers of M dense "
        "neuronal clusters, then M linear output neurons (Fig. 2)."),
      fig("aadrnn.png", W * 0.85, "Figure 2 — AADRNN-based IDS (team's re-drawing of Fig. 1 of [1])."),
      P("3.2 Traffic metrics (inputs)", "h2"),
      *bullets(["<b>Malicious traffic detection (M = 3):</b> total size of the last 500 packets, average inter-transmission time of the "
                "last 500 packets, and number of packets in the last 100 s.",
                "<b>Compromised device identification (M = 6, 10-s windows):</b> average size and number of packets from a single source, "
                "maximum size and number from any single source, and total size and number of packets transmitted."]),
      P("All metrics come from packet headers only. They are content-agnostic and device-agnostic, which helps privacy and keeps the "
        "computation small enough for lightweight nodes.")]

# ------------------------------------------------------------------ 4
E += [P("4. Proposed Methodology and Algorithms", "h1"), AUTH(),
      P("4.1 Detection (forward pass and decision)", "h2"),
      P("x̂<sub>(i,1)</sub> = ζ([x<sub>i</sub>, 1] W<sub>1</sub>),   x̂<sub>(i,h)</sub> = ζ([x̂<sub>(i,h−1)</sub>, 1] W<sub>h</sub>),   "
        "x̂<sub>i</sub> = [x̂<sub>(i,H−1)</sub>, 1] W<sub>H</sub>      (1)–(3)", "eq"),
      P("ζ(Λ) = [p(r+λ⁺)+λ⁻+Λ] / (2[λ⁻+Λ]) − √( ([p(r+λ⁺)+λ⁻+Λ] / (2[λ⁻+Λ]))² − λ⁺/(λ⁻+Λ) )      (4)", "eq"),
      P("y<sub>i</sub> = (1/M) Σ<sub>m</sub> |x<sub>mi</sub> − x̂<sub>mi</sub>|   (traffic)        "
        "y<sub>i</sub> = max<sub>m</sub> |x<sub>mi</sub> − x̂<sub>mi</sub>|   (device identification)      (5)–(6)", "eq"),
      P("4.2 Learning the AADRNN", "h2"),
      P("<b>Initial learning (l = 0):</b> each hidden layer is fitted with non-negative, L1-regularised least squares, solved by FISTA:"),
      P("W<sub>h</sub> = argmin<sub>W≥0</sub> ‖ [adj(ζ(X̂<sub>h−1</sub> W<sub>R</sub>)), 1] W − X̂<sub>h−1</sub> ‖² + ‖W‖<sub>1</sub>,    "
        "W<sub>h</sub> ← 0.1 W<sub>h</sub> / max(X̂<sub>h</sub>)      (7), (9)", "eq"),
      P("<b>Online incremental learning (l ≥ 1):</b> only the output layer is updated, using the OS-ELM recursive least-squares rule:"),
      P("O<sub>l</sub> = O<sub>l−1</sub> − O<sub>l−1</sub>X<sup>T</sup>(I + X O<sub>l−1</sub> X<sup>T</sup>)<sup>−1</sup> X O<sub>l−1</sub>,     "
        "W<sub>H</sub> ← W<sub>H</sub> + O<sub>l</sub> X<sup>T</sup>(X̂<sub>0</sub> − X W<sub>H</sub>),   X = X̂<sub>H−1</sub>      (10)–(12)", "eq"),
      P("The learning error passed to SSID is the mean IDS output over the batch, E(l) = (1/|B<sub>l</sub>|) Σ<sub>i∈B<sub>l</sub></sub> y<sub>i</sub>   (13)."),
      P("4.3 Self-supervised packet selection", "h2"),
      P("p⁺<sub>i</sub> = Γ y<sub>i</sub>,     p⁻<sub>i</sub> = Γ (1 − y<sub>i</sub>),     q<sub>i</sub> = 1 − Γ      (17)–(20)", "eq"),
      P("A packet becomes a benign training sample with probability p⁻, a malicious sample with probability p⁺, or is skipped with "
        "probability q. When trust is low, almost nothing is selected. The very first packet is assumed benign (p⁻ = 1)."),
      P("4.4 Trust coefficient", "h2"),
      P("Γ = C<sub>rep</sub> · C<sub>gen</sub>      (21)", "eq"),
      P("<b>Representativeness.</b> Inter-transmission times (TT) and packet lengths (PL) are assumed independent and exponential. "
        "For the learned set (rate λ<sub>l</sub>) and the observed-normal set (rate λ<sub>o</sub>), the KL divergence has a closed form:"),
      P("D<sup>TT</sup><sub>KL</sub> = log(λ<sub>o</sub>/λ<sub>l</sub>) − (λ<sub>o</sub>−λ<sub>l</sub>)/λ<sub>o</sub>,    "
        "C<sub>rep</sub> = ½ [ (λ<sub>l</sub>/λ<sub>o</sub>) e<super>−(λ<sub>l</sub>−λ<sub>o</sub>)/λ<sub>o</sub></super> + "
        "(μ<sub>l</sub>/μ<sub>o</sub>) e<super>−(μ<sub>l</sub>−μ<sub>o</sub>)/μ<sub>o</sub></super> ]      (23), (32)", "eq"),
      P("<b>Generalisation.</b> Generalisation is taken as \"data + knowledge\": C<sub>gen</sub> = ½Δ + ½κ (33). Here Δ = 1 − min(W / Σ<sub>k</sub>|B<sub>k</sub>|, 1) (34), "
        "with W the number of learnable parameters, and κ = 1 − Σ<sub>k=0..l</sub> (½)<super>l−k+1</super> E(k) (35), "
        "which can be updated recursively as κ ← ½ − ½(E(l) − κ) (36)."),
      P("4.5 Phase control", "h2"),
      *bullets(["<b>Initial learning (l = 0):</b> the parameters update for <i>every</i> selected packet. The phase ends when Γ ≥ Θ (14).",
                "<b>Online learning (l ≥ 1):</b> selected packets go into a batch B<sub>l</sub>. The model updates when Γ &lt; Θ, |B<sub>l</sub>| ≥ K, "
                "and the mean of the last I outputs is ≤ γ (15). If that mean exceeds γ, an attack is assumed and B<sub>l</sub> is emptied (16), "
                "so false negatives just before an alarm are not learned."]),
      P("Algorithm 1 — SSID main loop (team's pseudocode of §IV in [1])", "h3"),
      Preformatted("""Γ ← 0 ; l ← 0 ; B ← ∅ ; first packet labelled benign
for each arriving packet i:
    y_i ← IDS(x_i) ;  s_i ← mean(y_{i-I+1..i})            # detection, unchanged
    if s_i ≤ γ: add (TT_i, PL_i) to observed-normal statistics
    Γ ← C_rep · C_gen
    draw u ~ U(0,1): benign if u < Γ(1−y_i); malicious if u < Γ; else skip
    if l = 0:
        if benign: update IDS with packet i ; update C_gen with E
        if Γ ≥ Θ: l ← 1
    else:
        if benign: B ← B ∪ {i}
        if s_i > γ: B ← ∅                                   # attack: discard batch
        elif Γ < Θ and |B| ≥ K:
            update IDS on B (OS-ELM) ; update C_rep, C_gen ; l ← l+1 ; B ← ∅""", st["code"]),
      Spacer(1, 6),
      P("Parameter values used in [1]: Θ = 0.95, I = 10, K = 100, γ = 0.25, c<sub>1</sub> = c<sub>2</sub> = c<sub>3</sub> = c<sub>4</sub> = 0.5.")]

# ------------------------------------------------------------------ 5
E += [P("5. Experimental Setup and Key Findings of the Paper", "h1"), AUTH(),
      table([["Item", "Setting in [1]"],
             ["Datasets", "Kitsune Mirai: 764,137 packets, 107 IPs, ~7,137 s, 121,621 benign / 642,516 malicious. Kitsune SYN DoS "
                          "(2.77 M packets). Bot-IoT DDoS-HTTP/TCP/UDP and DoS-HTTP (19.8 k – 19.5 M packets)."],
             ["Tasks", "Malicious-traffic detection (M = 3) and compromised-device identification, CDIS (M = 6, 10-s windows)."],
             ["Baselines", "AADRNN and MLP with offline learning (first 83,000 benign packets) and with incremental learning "
                           "(retrained every 750 packets on own decisions, first 750 assumed benign); KNN and Lasso (offline); CDIS with sequential learning."],
             ["Metrics", "ROC, accuracy, TPR, TNR; balanced accuracy for CDIS."]],
            [3 * cm, 13.8 * cm]),
      P("Table 2 — Experimental setup reported in [1].", "cap"),
      P("Key findings reported by the authors", "h2"),
      *bullets(["SSID-AADRNN reaches <b>TPR &gt; 0.995 at FPR ≈ 10⁻⁵</b> on Kitsune-Mirai (ROC, Fig. 4 of [1]).",
                "Γ starts at 0, rises quickly, and accurately reflects how trustworthy the decisions are. The model is not updated while the attack is in progress (Fig. 5 of [1]).",
                "Learning fully online from only <b>4,161 packets</b>, SSID is competitive with AADRNN trained offline on about 83,000 packets, and it "
                "clearly beats incremental learning on all metrics (Fig. 6 of [1]).",
                "SSID-MLP has slightly higher accuracy and TPR than offline MLP, which however has 100% TNR (Fig. 7 of [1]). SSID-MLP is second-best among all models (Fig. 8 of [1]).",
                "SSID-CDIS matches sequential CDIS on Mirai and improves it on SYN DoS. On Bot-IoT it raises median balanced accuracy by "
                "<b>18% (DDoS-TCP)</b> and <b>11% (DDoS-UDP)</b> and by 2% on average for DoS-HTTP (Figs. 9–10 of [1]). It shows much higher TNR, "
                "but its average TPR is \"considerably low\" (Table II of [1])."]),
      TEAM(),
      P("<b>Do the results support the claims?</b> Partly. The claim of competitiveness with offline training is supported on the one "
        "Kitsune-Mirai trace. However, that trace is 84% malicious and the attack begins after a long benign period. This is the "
        "most favourable setting for a self-labelling scheme, because the model is fully trained before the attack starts, and the attack is "
        "abrupt, so it is flagged at once and never learned. The claim that SSID enables adaptation to time-varying traffic is "
        "<i>motivated</i> but never directly <i>tested</i>: no experiment contains a controlled benign drift. The CDIS results show that much of "
        "the gain comes from higher TNR, while TPR is low (Table II of [1]), so the improvement is in false alarms rather than in detection."),
      PageBreak()]

# ------------------------------------------------------------------ 6
E += [P("6. Critical Assessment", "h1"), TEAM(),
      P("This section is entirely our own analysis. Where we say an issue was <i>confirmed experimentally</i>, the evidence is in §8."),
      P("6.1 Strengths", "h2"),
      *bullets(["<b>Truly label-free and online:</b> no offline dataset, no human labelling, and a cold start of one packet. Few self-supervised IDSs manage this (Table 1).",
                "<b>Decides when to learn:</b> trust-triggered updates replace a hand-picked retraining interval. In our runs, SSID's steady state performs "
                "very few updates compared with periodic retraining.",
                "<b>Model-agnostic:</b> the same controller works with AADRNN, MLP and CDIS. We confirmed this with an MLP backbone.",
                "<b>Very lightweight:</b> it uses 3–6 header metrics, O(1) statistics for C<sub>rep</sub>, and OS-ELM updates of the output layer only. "
                "It is well suited to IoT gateways.",
                "<b>Batch clearing on alarm</b> (eq. 16) is a simple and effective defence against learning the packets just before an abrupt attack."]),
      P("6.2 Restrictive assumptions", "h2"),
      table([["Assumption", "Why it is restrictive", "Consequence"],
             ["First packet is benign; network clean at deployment", "An IDS is often deployed because a network is suspected compromised.",
              "If an infection is already present, it is learned as \"normal\" and never flagged."],
             ["TT and PL are exponential and independent", "IoT packet lengths are strongly multimodal (ACK ≈ 60 B vs. MTU 1,500 B), and "
              "inter-arrival times are bursty or periodic.", "C<sub>rep</sub> compares only <i>means</i>. Two very different distributions with equal means give C<sub>rep</sub> = 1."],
             ["Cumulative statistics", "λ<sub>l</sub>, λ<sub>o</sub> and κ average over the whole history.", "After months of operation, a drift barely moves the means, so C<sub>rep</sub> reacts slowly."],
             ["\"Observed normal\" = packets the IDS judged normal", "This uses the IDS's own decisions, the same quantity being trusted.",
              "Circular: C<sub>rep</sub> cannot reveal that the IDS is systematically wrong."],
             ["Fixed γ = 0.25", "y is a reconstruction error, so its scale depends on the normalisation of the metrics.", "γ has to be re-tuned for every metric set or normalisation, which contradicts the claim of no human intervention."],
             ["Data adequacy via W", "W counts all parameters, but only W<sub>H</sub> is updated online.", "Δ overstates the data needed in the online phase."]],
            [4.0 * cm, 6.4 * cm, 6.4 * cm]),
      P("Table 3 — Assumptions identified by the team.", "cap"),
      P("6.3 Technical drawbacks and errors found in the paper", "h2"),
      *bullets(["<b>Self-poisoning / boiling-frog vulnerability (confirmed experimentally).</b> Training labels come from the IDS's own outputs. An "
                "attacker can raise the attack intensity slowly, so each batch is only slightly more anomalous than what has been learned. "
                "Each batch stays below γ, gets accepted and learned, and the model of \"normal\" follows the attack. Batch clearing (16) cannot help "
                "because the alarm never fires. This is the main threat to any self-training IDS, and the paper does not discuss it.",
                "<b>Bootstrap deadlock (confirmed in implementation).</b> At l = 0 we have Δ = 0 (fewer than W samples), so C<sub>gen</sub> = ½κ = ¼(1 − E(0)). "
                "If the untrained IDS outputs y = 1 (an untrained detector reasonably reports \"unknown\" as maximum anomaly), then E(0) = 1, κ = 0, "
                "Γ = 0 and q = 1 forever: no packet is ever selected and learning never starts. Start-up only works because an untrained model "
                "outputs y &lt; 1 by chance. A related problem: C<sub>rep</sub> needs observed-normal statistics, but at start-up no packet is judged normal.",
                "<b>κ is biased upward.</b> The weights (½)<super>l−k+1</super> in (35) sum to 1 − 2<super>−(l+1)</super> &lt; 1. With a constant error E, "
                "κ = 1 − E(1 − 2<super>−(l+1)</super>). At l = 0, κ = 1 − E/2, which overstates knowledge exactly when the model knows least. We use the "
                "bias-corrected form κ = 1 − Σw<sub>k</sub>E(k) / Σw<sub>k</sub>.",
                "<b>Typos and inconsistencies.</b> (a) Eq. (38) reads [1 − min(·) + Σ(½)<super>l−k+1</super>E(k)]/2. From (37) it must be "
                "[2 − min(·) − Σ(½)<super>l−k+1</super>E(k)]/2. (b) Eq. (10) initialises O<sub>0</sub> with X̂<sub>H</sub> (the output), but (11)–(12) use "
                "the hidden output X̂<sub>H−1</sub>. (c) Eq. (28) is labelled D<sup>PL</sup> although it gives D<sup>TT</sup>. (d) The window in (15) is "
                "j = i−I+1..i (I packets), but in (16) it is j = i−I..i (I+1 packets). (e) O<sub>0</sub> = (X<sup>T</sup>X)<super>−1</super> is singular "
                "when fewer than M+1 samples have been learned, which is always the case at the start of l = 0. Regularisation is needed but not stated. "
                "(f) The discriminant in (4) is negative for small Λ, and no input domain is given.",
                "<b>Malicious selection (p⁺) is unused.</b> An auto-associative IDS learns only benign data, so the p⁺ branch only lowers the "
                "effective selection rate. The framework's symmetric formulation is not exploited.",
                "<b>No bottleneck in the AAM.</b> H = M layers of M units means the network can approach the identity map. "
                "Anomalies are then detected only through the saturation of ζ, and the online OS-ELM updates steadily make the "
                "network more permissive. This makes poisoning worse.",
                "<b>Unbounded batch memory.</b> While Γ ≥ Θ, nearly every packet is selected (p⁻ ≈ 0.95) but no update happens, so B<sub>l</sub> grows "
                "without limit. That is a problem on memory-constrained IoT nodes. We cap B at 5,000 packets."]),
      P("6.4 Gaps in the evaluation", "h2"),
      *bullets(["Malicious-traffic detection is evaluated on <b>one trace</b> (Kitsune-Mirai) that is <b>84% malicious</b>, so accuracy is inflated. "
                "There are no results over several runs, even though packet selection is random.",
                "<b>No sensitivity analysis</b> for Θ, γ, I and K, and no justification for γ = 0.25.",
                "<b>Missing baseline:</b> KitNET [17], an online unsupervised autoencoder IDS published with the same dataset. Also missing: "
                "streaming detectors such as Half-Space Trees or RRCF.",
                "The motivating case, <b>benign concept drift</b>, is never tested on its own, and neither are <b>adversarial</b> or gradual attacks.",
                "There are <b>no runtime, memory or energy measurements</b>, despite the IoT-lightweight claim.",
                "<b>Label granularity:</b> metrics are aggregated over 500 packets or 100 s, yet packets are scored with per-packet labels. Benign packets "
                "during an attack window inevitably look malicious. In our evaluation, FPR is measured on benign packets outside attack windows."]),
      P("6.5 Unresolved issues", "h2"),
      P("Several questions remain open. How should SSID tell benign drift from a slow attack, given that both look alike in these features? How should "
        "trust be calibrated against ground truth when a little labelled data exists? How can the AAM be kept from becoming "
        "more permissive after many online updates? And how should several SSID nodes share knowledge without sharing poisoned models (the federated "
        "extension the authors mention)?"),
      PageBreak()]

# ------------------------------------------------------------------ 7
E += [P("7. Proposed Improvements: SSID+", "h1"), TEAM(),
      P("Each change targets a limitation from §6, can be switched on or off independently (ablation in §8.5), and keeps "
        "SSID's main property: no labels and no offline data."),
      table([["#", "Change", "Limitation addressed", "Technical justification", "Expected benefit / challenge"],
             ["1", "Sliding-window Jensen–Shannon representativeness: C<sub>rep</sub> = 1 − ½[JS(TT) + JS(PL)] over 16-bin histograms of log TT and log PL, "
                   "on the last 3,000 learned and observed packets", "Exponential assumption; mean-only comparison; cumulative statistics",
              "JS divergence in base 2 is symmetric and bounded in [0,1], so it needs no e<super>−D</super> mapping. Histograms capture multimodality. A window keeps it responsive.",
              "Notices shape changes and reacts faster to drift. Costs O(bins) per evaluation, and the bin ranges must be chosen."],
             ["2", "Bias-corrected κ = 1 − Σw<sub>k</sub>E(k) / Σw<sub>k</sub>", "Upward bias of (35)",
              "This is a proper weighted mean, so κ = 1 − E for a constant error.", "Trust is no longer inflated early on. Bootstrapping is slightly slower."],
             ["3", "Confidence-gated pseudo-labelling: accept as benign only if y<sub>i</sub> ≤ min(γ/2, μ<sub>acc</sub> + 3σ<sub>acc</sub>)",
              "Self-poisoning; confirmation bias", "This is the confident-learning principle used in self-training: learn only from high-confidence pseudo-labels. "
              "The bound follows the IDS's own accepted outputs.", "Stops ambiguous packets from being learned. Too strict a gate slows adaptation to abrupt benign drift."],
             ["4", "Adaptive intrusion threshold γ<sub>t</sub> = clip(μ<sub>acc</sub> + kσ<sub>acc</sub>, 0.03, γ), k = 6",
              "Scale-dependent fixed γ; slow ramp stays under 0.25", "The alarm threshold is set relative to the IDS's own benign error distribution, like a control chart.",
              "No tuning per metric set. An attack is flagged as soon as it leaves the benign error band, so its batches are cleared by (16)."],
             ["5", "Forgetting-factor OS-ELM (λ<sub>f</sub> = 0.995)", "Equal weight on all history slows adaptation",
              "This is standard FOS-ELM / exponentially weighted RLS.", "Faster tracking of drift. Used alone it would make poisoning easier, so it is paired with 3 and 4."]],
            [0.6 * cm, 3.9 * cm, 3.0 * cm, 4.8 * cm, 4.5 * cm]),
      P("Table 4 — SSID+ components.", "cap"),
      P("7.1 Further extensions (proposed, not implemented)", "h2"),
      *bullets(["<b>Drift-versus-attack discrimination</b> with a sequential change detector (Page–Hinkley or ADWIN) on each metric. Drift that keeps "
                "the <i>shape</i> of benign traffic (for example, packet-size mix) could be learned, while a shift in direction toward known attack "
                "signatures (tiny packets, high rate) is held back for confirmation.",
                "<b>Anchor memory:</b> keep a small reservoir of early, high-confidence benign samples and reject any update that worsens reconstruction "
                "on the anchors by more than a margin. This is a safeguard against catastrophic poisoning.",
                "<b>Federated SSID</b> (the authors' future work): nodes share Γ-weighted output-layer updates, with robust aggregation (median or trimmed mean) "
                "so that one poisoned node cannot spread its model.",
                "<b>Bottleneck AAM</b> (M → M−1 → M) or a KitNET-style ensemble, to stop the auto-associative memory from drifting toward the identity map.",
                "<b>Semi-supervised calibration:</b> when a few labelled packets exist, use them as the validation set that the paper's κ allows for but never uses."])]

# ------------------------------------------------------------------ 8
def res_table(sc):
    meths = ["Offline-AADRNN", "Incremental-AADRNN", "Offline-KNN", "Offline-IForest",
             "SSID-AADRNN (paper)", "SSID-MLP (paper)", "SSID+ (ours)"]
    rows = [["Method", "TPR", "TNR", "Balanced acc.", "AUC", "Packets learned", "µs / packet"]]
    for n in meths:
        d = S[sc][n]
        lr = d["learned"][0]
        rows.append([("<b>%s</b>" % n) if "ours" in n else n, ms(sc, n, "TPR"), ms(sc, n, "TNR", 4), ms(sc, n, "BalAcc"),
                     m(sc, n, "AUC", 4), "-" if lr != lr else f"{lr:,.0f}", f"{d['us_per_pkt'][0]:.1f}"])
    return table(rows, [3.4 * cm, 2.3 * cm, 2.9 * cm, 2.3 * cm, 1.5 * cm, 2.1 * cm, 1.8 * cm])


E += [PageBreak(), P("8. Implementation and Experimental Validation", "h1"), TEAM(),
      P("8.1 Implementation", "h2"),
      P("We implemented the full pipeline from scratch in Python (NumPy, scikit-learn, Matplotlib). The code is in <i>3_Source_Code/</i>, and "
        "each line of the SSID loop is annotated with the matching equation number of [1]."),
      table([["File", "Content"],
             ["ssid/traffic.py", "Scenario generator; real-packet CSV loader; causal extraction of the 3 metrics (vectorised, O(n))."],
             ["ssid/models.py", "DRNN activation ζ (eq. 4), FISTA for non-negative L1 least squares (eq. 7), AADRNN with OS-ELM (eqs. 10–12) and an optional "
                                "forgetting factor; M-M-M-M sigmoid MLP auto-encoder with Adam; decision maker (eq. 5)."],
             ["ssid/framework.py", "SSID controller (eqs. 13–38) with SSID+ switches; offline and incremental baselines."],
             ["run_experiments.py", "All scenarios × seeds × methods, ablation, Θ×γ sensitivity, tables and figures."],
             ["pcap_to_csv.py", "Converts Kitsune/Bot-IoT pcaps and labels into the CSV used by --csv (to run on the real datasets)."]],
            [3.6 * cm, 13.2 * cm]),
      P("<b>Implementation choices not specified in the paper</b> (documented in the code): (i) a ridge term of 10⁻³ in O<sub>0</sub>, because it is singular with few samples; "
        "(ii) the inputs to the hidden layers are min-max scaled with statistics frozen at the last initial fit, because with low-variance inputs the non-negative L1 "
        "problem (7) collapses onto the bias row and the hidden layers carry no information; (iii) the last hidden layer is standardised before the "
        "linear output layer; (iv) an untrained model outputs y = 0.5 (with y = 1 the bootstrap deadlocks, §6.3); (v) during l = 0 every "
        "packet counts as observed traffic for C<sub>rep</sub>; (vi) during l = 0 the hidden layers are refitted at |B<sub>0</sub>| = 2<super>k</super> and every 100 "
        "packets, with OS-ELM updates in between; (vii) the batch B is capped at 5,000; (viii) the first 500 packets are skipped "
        "so the 500-packet metric window is full."),
      P("8.2 Experimental setup", "h2"),
      P("<b>Data.</b> Kitsune and Bot-IoT need registration and several GB of pcap, so we evaluate on a reproducible <b>synthetic IoT trace generator</b> "
        "built to recreate the conditions that matter for SSID. The trace lasts 3,000 s and has six benign devices with Poisson arrivals and bimodal packet "
        "lengths (control packets ≈ 66 B, data packets 90 B + an exponential component). The attack phase (last third) uses a Mirai-like flood at 60 packets/s of 54–80 B "
        "scan/SYN packets. There are three scenarios: <b>mirai</b> (stationary benign traffic and an abrupt attack, close to the paper's setting); "
        "<b>mirai_drift</b> (four new camera-like devices join one at a time in the middle third: benign concept drift); and "
        "<b>slow_ramp</b> (drift plus an attack whose rate ramps linearly from 0 to 60 packets/s over 900 s, an adversarial \"boiling-frog\" test). "
        "Each scenario has about 60–90 k packets and is run with <b>5 random seeds</b>."),
      P("<b>Baselines</b>, following the paper's protocol as closely as possible: Offline-AADRNN, Offline-KNN (mean 5-NN distance) and Offline-IForest, all trained on "
        "the first 5,000 <i>oracle-labelled</i> benign packets; Incremental-AADRNN (first 750 packets assumed benign, then retrained every 750 packets on packets it judged "
        "benign); SSID-AADRNN and SSID-MLP with the paper's parameters (Θ = 0.95, I = 10, K = 100, γ = 0.25); and SSID+ (ours). "
        "<b>Metrics:</b> TPR on attack packets; TNR on benign packets <i>outside</i> attack windows (see §6.4); balanced accuracy, which handles class imbalance; "
        "threshold-free ROC-AUC; packets learned; and processing time per packet (Apple-silicon laptop, single thread, Python)."),
      KeepTogether([P("8.3 Results", "h2"), P("Scenario mirai (abrupt attack, no drift)", "h3"), res_table("mirai"),
      P("Table 5 — Mean ± std over 5 seeds.", "cap"),]),
      KeepTogether([P("Scenario mirai_drift (gradual benign drift, then abrupt attack)", "h3"), res_table("mirai_drift"),
      P("Table 6 — Mean ± std over 5 seeds.", "cap"),]),
      KeepTogether([P("Scenario slow_ramp (gradual drift, then slowly ramping attack)", "h3"), res_table("slow_ramp"),
      P("Table 7 — Mean ± std over 5 seeds.", "cap"),]),
      fig("balacc_comparison.png", W, "Figure 3 — Balanced accuracy (mean ± std over 5 seeds) for all methods and scenarios."),
      P("8.4 Discussion", "h2"),
      *bullets([f"<b>The paper's claims reproduce in its own setting.</b> On <i>mirai</i>, SSID-AADRNN reaches balanced accuracy {m('mirai','SSID-AADRNN (paper)','BalAcc')} "
                f"and AUC {m('mirai','SSID-AADRNN (paper)','AUC',4)}, after learning from only about {S['mirai']['SSID-AADRNN (paper)']['learned'][0]:.0f} packets with no labels. "
                "This matches the offline model's AUC, which used 5,000 oracle-labelled packets. Incremental learning collapses (TPR ≈ 0) because it retrains on attack windows. "
                "This agrees with the paper's Fig. 6.",
                "<b>A fixed γ is fragile for offline models.</b> Offline-AADRNN has high AUC but very variable TPR (0.77 ± 0.39) at γ = 0.25. "
                "The ranking is good; the threshold is not. This supports our point that γ depends on scale.",
                f"<b>Benign drift.</b> The offline KNN and IForest detectors, which cannot adapt, flag almost all post-drift benign traffic (TNR ≈ 0.35–0.40). "
                f"SSID tracks the drift with zero false positives in the drift phase, which <i>confirms the paper's main motivation</i>. That motivation was not tested in [1]. "
                f"SSID+ also improves TPR from {m('mirai_drift','SSID-AADRNN (paper)','TPR')} to {m('mirai_drift','SSID+ (ours)','TPR')}.",
                f"<b>Self-poisoning.</b> In <i>slow_ramp</i>, both of the paper's SSID variants learn the attack as normal: TPR is {m('slow_ramp','SSID-AADRNN (paper)','TPR')} (AADRNN) "
                f"and {m('slow_ramp','SSID-MLP (paper)','TPR')} (MLP), and the learned set grows to about {S['slow_ramp']['SSID-AADRNN (paper)']['learned'][0]:,.0f} packets. "
                "Fig. 4 shows the mechanism: the IDS output climbs with the attack but stays just below γ, Γ dips, an update is triggered, and the output "
                f"collapses back near 0 while the attack is still running. SSID+ keeps detecting the attack (TPR {ms('slow_ramp','SSID+ (ours)','TPR')}) with "
                "unchanged TNR, because its adaptive threshold (≈0.09 here) fires early, so the attack batches are cleared by (16) and never learned.",
                "<b>Cost.</b> SSID+ is roughly 3–6× slower per packet in our Python code, mostly because of the JS histograms. At about 40–100 µs per packet "
                "it can still handle more than 10,000 packets/s on one core, and a C implementation would remove most of the overhead."]),
      fig("timeline_slow_ramp.png", W, "Figure 4 — Slow-ramp scenario, seed 0: IDS output, trust Γ and intrusion threshold over time. "
          "Top: the paper's SSID absorbs the attack at t ≈ 2,500 s. Bottom: SSID+ keeps the attack above its adaptive threshold (style follows Fig. 5 of [1])."),
      fig("timeline_mirai_drift.png", W * 0.92, "Figure 5 — Drift scenario: both frameworks follow the benign drift (new devices at 1,000–1,600 s) without false alarms."),
      KeepTogether([P("8.5 Ablation study", "h2"),
      P("Each SSID+ component was added on its own to the paper's SSID (slow_ramp scenario, 5 seeds):"), table([["Variant", "TPR", "Balanced acc.", "Packets learned"]] +
            [[n, ms("slow_ramp", n, "TPR"), ms("slow_ramp", n, "BalAcc"), f"{S['slow_ramp'][n]['learned'][0]:,.0f}"]
             for n in ["SSID-AADRNN (paper)", "SSID + gate", "SSID + adaptive-gamma", "SSID + JS-rep", "SSID + unbiased-kappa",
                       "SSID + forgetting", "SSID+ (ours)"]],
            [5.5 * cm, 3.6 * cm, 3.6 * cm, 3.0 * cm]),
      P("Table 8 — Ablation on slow_ramp.", "cap")]),
      P("The <b>adaptive threshold</b> contributes most on its own (TPR 0.96). The <b>confidence gate</b> helps partly (0.34, with high variance). "
        "JS representativeness and forgetting do not resist poisoning by themselves. They exist to make adaptation faster, and alone they "
        "even increase the amount learned. The full combination gives the highest TPR with the lowest variance and learns about 3× fewer packets, so gating and the "
        "adaptive threshold cover each other's weaknesses. In short, poisoning resistance comes from <i>what</i> gets learned (gate, γ<sub>t</sub>), "
        "and the other components only change <i>how fast</i> learning happens."),
      fig("ablation_slow_ramp.png", W * 0.8, "Figure 6 — Ablation: TPR on the slow-ramp attack."),
      P("8.6 Hyper-parameter sensitivity of the paper's SSID", "h2"),
      P(f"Over Θ ∈ {{0.90, 0.95, 0.98}} × γ ∈ {{0.10, 0.25, 0.40}} on <i>mirai_drift</i> (3 seeds), the balanced accuracy of SSID ranges from "
        f"{min(min(r) for r in SENS):.3f} to {max(max(r) for r in SENS):.3f}. γ = 0.40 breaks detection completely (≈0.5), and moving Θ away from 0.95 costs "
        "about 10 points. The paper's choice works well here, but the result depends strongly on parameters the paper presents as fixed. This supports both the "
        "\"no human intervention\" critique and the adaptive-γ proposal."),
      fig("sensitivity_theta_gamma.png", W * 0.5, "Figure 7 — Sensitivity of the paper's SSID to Θ and γ."),
      P("8.7 Threats to validity", "h2"),
      P("Our numbers come from a synthetic generator, not from Kitsune or Bot-IoT, so they show <i>mechanisms</i> (adaptation, poisoning) rather than "
        "absolute performance on those datasets. The metric normalisation (log ranges) is our own, and γ depends on it. The AADRNN needed "
        "conditioning choices (§8.1) that may differ from the authors' code. The slow-ramp attack is deliberately adversarial. We provide "
        "<i>pcap_to_csv.py</i> so the exact same pipeline can be run on the real Kitsune-Mirai capture.")]

# ------------------------------------------------------------------ 9
E += [P("9. Conclusion", "h1"),
      P("<font color='#B45309'>■ Authors:</font> SSID shows that a deep anomaly-based IDS can train itself fully online from its own trust-weighted decisions. "
        "It needs no offline data or labels, adapts to traffic changes, and is competitive with offline training on Kitsune-Mirai and Bot-IoT."),
      P("<font color='#0F766E'>■ Team:</font> Our re-implementation confirms these claims for abrupt attacks and for gradual benign drift, which the paper motivates but "
        "does not test. We also show that the self-labelling loop has a serious blind spot: a slowly ramping attack is learned as normal "
        "(TPR ≈ 0). We found a bootstrap deadlock, an upward bias in κ, several equation typos, restrictive traffic assumptions and gaps in the evaluation. "
        "Our SSID+ variant combines distribution-free windowed representativeness, a bias-corrected κ, confidence-gated pseudo-labels, an adaptive threshold "
        "and a forgetting factor. It closes the poisoning gap (TPR 0.985) without losing performance elsewhere. The remaining open problem is telling "
        "abrupt <i>benign</i> drift from an attack without labels. We see change detection, anchor memories and robust federated aggregation as the next steps."),
      P("References", "h1"),
      *[P(r, "bul") for r in [
          "[1] M. Nakıp and E. Gelenbe, “Online self-supervised deep learning for intrusion detection systems,” IEEE Trans. Inf. Forensics Security, vol. 19, pp. 5668–5683, 2024.",
          "[7] M. Nakıp and E. Gelenbe, “Botnet attack detection with incremental online learning,” in Security in Computer and Information Sciences, Springer, 2022.",
          "[8] E. Gelenbe and M. Nakıp, “Traffic based sequential learning during botnet attacks to identify compromised IoT devices,” IEEE Access, vol. 10, 2022.",
          "[17] Y. Mirsky, T. Doitshman, Y. Elovici and A. Shabtai, “Kitsune: An ensemble of autoencoders for online network intrusion detection,” NDSS, 2018.",
          "[18] N. Koroniotis et al., “Towards the development of realistic botnet dataset in the Internet of Things: Bot-IoT,” FGCS, vol. 100, 2019.",
          "[48] E. Gelenbe and Y. Yin, “Deep learning with random neural networks,” IJCNN, 2016.",
          "[58] A. Beck and M. Teboulle, “A fast iterative shrinkage-thresholding algorithm for linear inverse problems,” SIAM J. Imaging Sci., 2009.",
          "[59] N.-Y. Liang et al., “A fast and accurate online sequential learning algorithm for feedforward networks,” IEEE Trans. Neural Netw., 2006.",
          "[T1] J. Lin, “Divergence measures based on the Shannon entropy,” IEEE Trans. Inf. Theory, vol. 37, no. 1, 1991. (JS divergence, SSID+)",
          "[T2] B. Biggio and F. Roli, “Wild patterns: Ten years after the rise of adversarial machine learning,” Pattern Recognition, vol. 84, 2018. (poisoning)",
          "[T3] A. Bifet and R. Gavaldà, “Learning from time-changing data with adaptive windowing (ADWIN),” SDM, 2007. (drift detection)",
          "[T4] J.-S. Lim, “Partitioned online sequential extreme learning machine / forgetting-factor OS-ELM,” Neurocomputing, 2013. (forgetting OS-ELM)",
          "[T5] E. Arazo et al., “Pseudo-labeling and confirmation bias in deep semi-supervised learning,” IJCNN, 2020. (confidence gating)"]],
      P("Reference numbers [1]–[66] follow the analysed paper; [T1]–[T5] are additional references used by the team. Figures 1–2 are the team's re-drawings of "
        "figures in [1]. All result figures and tables in §8 are the team's own.", "cap"),
      P("Appendix A — Reproducing the results", "h1"),
      Preformatted("""cd 3_Source_Code
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python make_diagrams.py                 # architecture figures
python run_experiments.py --quick       # 1 seed  (~3 min)
python run_experiments.py               # 5 seeds + ablation + sensitivity (~15 min)
# real data (optional):
tshark -r Mirai_pcap.pcap -T fields -e frame.time_epoch -e frame.len -E separator=, > f.csv
python pcap_to_csv.py f.csv Mirai_labels.csv kitsune.csv && python run_experiments.py --csv kitsune.csv""", st["code"]),
      P("Appendix B — Individual contributions", "h1"),
      table([["Member", "Contribution (fill in)"], ["&lt;Member 1&gt;", "§1–2, slides 1–6, video part A"],
             ["&lt;Member 2&gt;", "§3–4, Algorithm 1, slides 7–12, video part B"],
             ["&lt;Member 3&gt;", "§5–6, error analysis of equations, slides 13–19, video part C"],
             ["&lt;Member 4&gt;", "§7–8, code, experiments, slides 20–27, video part D"]], [4 * cm, 12.8 * cm])]

doc = Doc(OUT, title="SSID Research Paper Analysis", author="Team")
doc.multiBuild(E)
print("built", OUT)
