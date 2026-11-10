const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");
const SKILL = process.argv[2];
const ROOT = process.argv[3];
const OUT = process.argv[4];
const { applyTheme } = require(path.join(SKILL, "scripts/apply_theme.js"));
const FIG = path.join(ROOT, "3_Source_Code/results/figures");
const S = JSON.parse(fs.readFileSync(path.join(ROOT, "3_Source_Code/results/summary.json"), "utf8").replace(/NaN/g, "null"));

const THEME = {
  name: "SSID Analysis",
  headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "111827", lt1: "FFFFFF", dk2: "0B2530", lt2: "F1F5F4",
    accent1: "0F766E", accent2: "B45309", accent3: "334155", accent4: "14B8A6",
    accent5: "D97706", accent6: "B91C1C", hlink: "0F766E", folHlink: "B45309" },
};
const H = { teal: "0F766E", amber: "B45309", ink: "111827", slate: "334155", muted: "6B7280",
  light: "F1F5F4", red: "B91C1C", grid: "E5E7EB", mint: "CCFBF1", sand: "FEF3C7", white: "FFFFFF", dark: "0B2530" };

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Online Self-Supervised Deep Learning for IDS - Analysis";
pres.author = "Team";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

pres.defineSlideMaster({ title: "TITLE", background: { color: H.dark },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.35, w: 8.8, h: 1.6,
    fontSize: 34, bold: true, color: C.background1, valign: "top", align: "left", fontFace: "Cambria" }, text: "" } }] });
pres.defineSlideMaster({ title: "SECTION", background: { color: H.dark },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.6, y: 2.0, w: 8.8, h: 1.0,
    fontSize: 36, bold: true, color: C.background1, align: "left", fontFace: "Cambria" }, text: "" } }],
  slideNumber: { x: 9.2, y: 5.2, w: 0.5, h: 0.3, fontSize: 9, color: "9CA3AF" } });
pres.defineSlideMaster({ title: "CONTENT", background: { color: H.white },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.28, w: 9.0, h: 0.7,
      fontSize: 26, bold: true, color: C.text1, valign: "middle", align: "left", fontFace: "Cambria", margin: 0 }, text: "" } },
    { text: { text: "Nakıp & Gelenbe, IEEE TIFS 2024 — research paper analysis", options: { x: 0.5, y: 5.25, w: 6, h: 0.25, fontSize: 9, color: "9CA3AF", margin: 0 } } },
  ],
  slideNumber: { x: 9.2, y: 5.22, w: 0.5, h: 0.3, fontSize: 9, color: "9CA3AF" } });

let sec = "Intro";
function slide(master, title, notes) {
  const s = pres.addSlide({ masterName: master, sectionTitle: sec });
  if (title) s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
}
function section(t, sub, notes) {
  sec = t; pres.addSection({ title: t });
  const s = slide("SECTION", t, notes);
  if (sub) s.addText(sub, { x: 0.6, y: 3.0, w: 8.8, h: 0.6, fontSize: 16, color: "99F6E4", isTextBox: true, margin: 0 });
  return s;
}
function tag(s, who, x = 0.5, y = 0.98) {
  const ours = who === "team";
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: ours ? 1.55 : 1.85, h: 0.26, rectRadius: 0.08,
    fill: { color: ours ? H.mint : H.sand }, line: { color: ours ? H.teal : H.amber, width: 0.75 }, objectName: "source-tag" });
  s.addText(ours ? "TEAM'S ANALYSIS" : "AUTHORS' CONTRIBUTION", { x, y, w: ours ? 1.55 : 1.85, h: 0.26, fontSize: 9, bold: true,
    color: ours ? H.teal : H.amber, align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function card(s, x, y, w, h, head, body, color = H.teal, fill = H.light, fs = 13) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: fill }, objectName: "card" });
  s.addText(head, { x: x + 0.18, y: y + 0.12, w: w - 0.36, h: 0.36, fontSize: 15, bold: true, color, margin: 0, isTextBox: true, valign: "top" });
  s.addText(body, { x: x + 0.18, y: y + 0.52, w: w - 0.36, h: h - 0.62, fontSize: fs, color: H.ink, margin: 0, isTextBox: true, valign: "top", paraSpaceAfter: 4 });
}
function num(s, x, y, n, color = H.teal) {
  s.addShape(pres.shapes.OVAL, { x, y, w: 0.42, h: 0.42, fill: { color }, line: { color }, objectName: "num-circle" });
  s.addText(String(n), { x, y, w: 0.42, h: 0.42, fontSize: 14, bold: true, color: H.white, align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function bullets(s, items, opt) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })),
    Object.assign({ fontSize: 14, color: H.ink, paraSpaceAfter: 6, valign: "top", isTextBox: true, margin: 0 }, opt));
}
function img(s, file, x, y, w, h, alt) {
  s.addImage({ path: path.join(FIG, file), x, y, w, h, altText: alt, sizing: { type: "contain", w, h } });
}
function eq(s, text, x, y, w, h, fs = 15) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: H.light }, line: { color: H.light }, objectName: "eq-box" });
  s.addText(text, { x: x + 0.15, y, w: w - 0.3, h, fontSize: fs, color: H.ink, valign: "middle", align: "center", margin: 0, isTextBox: true, fontFace: "Cambria" });
}
function tbl(s, rows, x, y, w, colW, fs = 11) {
  const data = rows.map((r, i) => r.map(c => ({ text: String(c), options: {
    bold: i === 0, color: i === 0 ? H.white : H.ink, fill: { color: i === 0 ? H.slate : (i % 2 ? H.white : H.light) } } })));
  s.addTable(data, { x, y, w, colW, fontSize: fs, border: { type: "solid", color: "D1D5DB", pt: 0.5 }, margin: 0.05, valign: "middle" });
}
const f3 = v => v.toFixed(3);
const g = (sc, m, k) => S[sc][m][k][0];

// ======================================================================= 1
pres.addSection({ title: "Intro" });
{ const s = slide("TITLE", "Online Self-Supervised Deep Learning for Intrusion Detection Systems",
  "Introduce the team and the paper. Say who covers which part (problem, method, critique, implementation).");
  s.addText("Research paper analysis · critical assessment · SSID+ improvements · experimental validation",
    { x: 0.6, y: 3.05, w: 8.8, h: 0.4, fontSize: 15, color: "99F6E4", isTextBox: true, margin: 0 });
  s.addText("Paper: M. Nakıp & E. Gelenbe, IEEE Transactions on Information Forensics and Security, vol. 19, pp. 5668–5683, 2024",
    { x: 0.6, y: 3.6, w: 8.8, h: 0.35, fontSize: 12, color: "D1D5DB", isTextBox: true, margin: 0 });
  s.addText("Team: <Member 1> · <Member 2> · <Member 3> · <Member 4>",
    { x: 0.6, y: 4.5, w: 8.8, h: 0.35, fontSize: 13, color: H.white, isTextBox: true, margin: 0 }); }

{ const s = slide("CONTENT", "Roadmap", "Walk through the five parts of the talk.");
  const parts = [["Problem & motivation", "Botnets, IoT, why online learning is hard"], ["SSID methodology", "AADRNN, trust Γ, packet selection, phases"],
    ["Paper's evaluation", "Kitsune & Bot-IoT setup and reported results"], ["Critical assessment", "Assumptions, errors, gaps, self-poisoning"],
    ["SSID+ & experiments", "Our 5 fixes, implementation, results"]];
  parts.forEach((p, i) => { const y = 1.15 + i * 0.8; num(s, 0.6, y, i + 1, i < 3 ? H.amber : H.teal);
    s.addText(p[0], { x: 1.2, y: y - 0.02, w: 4, h: 0.3, fontSize: 16, bold: true, color: H.ink, margin: 0, isTextBox: true });
    s.addText(p[1], { x: 1.2, y: y + 0.27, w: 4.5, h: 0.28, fontSize: 12, color: H.muted, margin: 0, isTextBox: true }); });
  card(s, 6.1, 1.15, 3.4, 3.6, "Colour code", "Amber tags: content summarised from the original authors.\n\nTeal tags: the team's own analysis, proposals and results.", H.slate); }

// ======================================================================= Problem
section("1 · Problem & Motivation", "Why does an IoT IDS need to learn online, without labels?",
  "Member 1 starts here.");
{ const s = slide("CONTENT", "Botnets turn cheap IoT devices into DDoS weapons",
  "Mirai-type malware compromises IoT devices, which then launch DDoS, leak data and spread malware. Two tasks: detect malicious traffic (reactive) and identify compromised devices (preventive).");
  tag(s, "authors");
  [["27.7%", "of global web traffic in 2021 came from malicious bots"], ["≈52%", "of IoT connections go to low-cost, low-maintenance devices"], ["2 tasks", "detect malicious traffic · identify compromised devices"]]
    .forEach((st, i) => { const x = 0.5 + i * 3.05;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.5, w: 2.8, h: 2.2, rectRadius: 0.1, fill: { color: H.light }, line: { color: H.light }, objectName: "stat" });
      s.addText(st[0], { x, y: 1.65, w: 2.8, h: 0.9, fontSize: 40, bold: true, color: H.teal, align: "center", fontFace: "Cambria", margin: 0, isTextBox: true });
      s.addText(st[1], { x: x + 0.2, y: 2.6, w: 2.4, h: 0.9, fontSize: 13, color: H.ink, align: "center", valign: "top", margin: 0, isTextBox: true }); });
  s.addText("Anomaly-based IDSs catch zero-day attacks, but they depend on a model of normal traffic, and normal traffic drifts.",
    { x: 0.5, y: 4.1, w: 9, h: 0.5, fontSize: 14, italic: true, color: H.slate, margin: 0, isTextBox: true }); }

{ const s = slide("CONTENT", "Two obstacles to online learning",
  "Obstacle 1: no labelled data per deployment. Obstacle 2: choosing when to retrain. Frequent retraining wastes compute; rare retraining leaves the model stale.");
  tag(s, "authors");
  card(s, 0.5, 1.45, 4.35, 2.9, "1 · No labelled data", "Each network needs its own collected and labelled traffic, which is rarely available.\n\nHuman labelling is slow, costly and error-prone.", H.amber, H.light, 16);
  card(s, 5.15, 1.45, 4.35, 2.9, "2 · When to update?", "Frequent updates burn scarce IoT compute for little gain.\n\nRare updates leave the model stale and false alarms rise after drift (e.g. new devices).", H.amber, H.light, 16); }

{ const s = slide("CONTENT", "Existing self-supervised IDSs still need offline data",
  "Summarise Table I of the paper. Point out that SSID is the only one that is fully online. Then the team's note: KitNET, which is online and unsupervised, is missing from the comparison.");
  tag(s, "authors");
  tbl(s, [["Work", "Mechanism", "Offline data", "Extra model", "Online"],
    ["Song & Kim", "LSTM pseudo-normal data", "Yes", "Yes", "No"], ["Wang et al.", "BYOL contrastive", "Yes", "Yes", "No"],
    ["Zhang et al.", "Bidirectional GAN", "Yes", "Yes", "No"], ["Caville et al.", "GNN contrastive", "Yes", "Yes", "No"],
    ["Abououf et al.", "LSTM-AE (cloud)", "Yes", "No", "Partly"], ["SSID (this paper)", "Own decisions × trust Γ", "No", "No", "Yes"]],
    0.5, 1.4, 6.2, [1.5, 1.95, 0.95, 0.95, 0.85], 11);
  card(s, 7.0, 1.4, 2.5, 2.8, "Team note", "KitNET, Kitsune's own detector, is an online unsupervised autoencoder IDS on the same dataset, and it is not compared.", H.teal, "ECFDF5"); }

{ const s = slide("CONTENT", "What the paper contributes",
  "Read out the contributions.");
  tag(s, "authors");
  const c = [["SSID framework", "Fully online, label-free training for any IDS with learnable parameters"],
    ["Trust coefficient Γ", "Γ = C_rep · C_gen measures online how far the IDS can be trusted"],
    ["Self-supervised selection", "Packets labelled with probabilities Γ(1−y) / Γy / 1−Γ"],
    ["Trust-triggered updates", "Retrain only when Γ < Θ and no attack is in progress"],
    ["Evaluation", "Kitsune + Bot-IoT, AADRNN & MLP backbones, two tasks"]];
  c.forEach((r, i) => { const y = 1.4 + i * 0.75; num(s, 0.6, y, i + 1, H.amber);
    s.addText(r[0], { x: 1.2, y: y - 0.02, w: 3.0, h: 0.45, fontSize: 15, bold: true, color: H.ink, margin: 0, valign: "middle", isTextBox: true });
    s.addText(r[1], { x: 4.2, y: y - 0.02, w: 5.3, h: 0.45, fontSize: 13, color: H.slate, margin: 0, valign: "middle", isTextBox: true }); }); }

// ======================================================================= Method
section("2 · SSID Methodology", "System model, AADRNN, trust coefficient, phases", "Member 2 starts here.");
{ const s = slide("CONTENT", "The IDS: an auto-associative Deep Random Neural Network",
  "AADRNN reconstructs the benign metrics it expects. y is the mean absolute deviation (eq. 5); device identification uses the max (eq. 6). Inputs are header-only metrics.");
  tag(s, "authors");
  img(s, "aadrnn.png", 0.4, 1.35, 5.6, 2.25, "AADRNN diagram");
  card(s, 6.2, 1.35, 3.3, 3.6, "Inputs (header only)", "Traffic detection, M = 3:\n• total size of last 500 pkts\n• mean inter-arrival of last 500\n• # pkts in last 100 s\n\nDevice identification, M = 6, over 10-s windows", H.amber);
  eq(s, "y_i = (1/M) Σ |x_mi − x̂_mi|  ·  alarm if mean(y, I = 10) > γ", 0.4, 3.85, 5.6, 0.7, 14); }

{ const s = slide("CONTENT", "Learning the AADRNN",
  "Initial phase: hidden layers fitted by non-negative L1 least squares solved with FISTA (eq. 7). Online phase: only the output layer is updated, using OS-ELM recursive least squares (eqs. 10–12).");
  tag(s, "authors");
  s.addText("Initial learning (l = 0): hidden layers by FISTA", { x: 0.5, y: 1.4, w: 9, h: 0.3, fontSize: 15, bold: true, color: H.amber, margin: 0, isTextBox: true });
  eq(s, "W_h = argmin_{W ≥ 0} ‖ [adj(ζ(X_{h−1} W_R)), 1] W − X_{h−1} ‖² + ‖W‖₁        (7)", 0.5, 1.8, 9, 0.6);
  s.addText("Online learning (l ≥ 1): output layer only, by OS-ELM", { x: 0.5, y: 2.65, w: 9, h: 0.3, fontSize: 15, bold: true, color: H.amber, margin: 0, isTextBox: true });
  eq(s, "O_l = O_{l−1} − O_{l−1}Xᵀ(I + X O_{l−1} Xᵀ)⁻¹ X O_{l−1}      W_H ← W_H + O_l Xᵀ(X₀ − X W_H)     (11–12)", 0.5, 3.05, 9, 0.6, 13.5);
  s.addText("ζ(·) is the DRNN dense-cluster activation (eq. 4). E(l) = mean of y over the learned batch (eq. 13) is passed back to SSID.",
    { x: 0.5, y: 3.9, w: 9, h: 0.6, fontSize: 13, color: H.slate, margin: 0, isTextBox: true }); }

{ const s = slide("CONTENT", "SSID: a learning line in parallel with detection",
  "Detection is unchanged. The learning line reads y, computes trust, selects packets, and decides when to update. The teal box previews our SSID+ changes.");
  tag(s, "authors");
  img(s, "ssid_architecture.png", 0.5, 1.3, 9.0, 3.85, "SSID architecture diagram"); }

{ const s = slide("CONTENT", "Self-supervised packet selection, weighted by trust",
  "Each packet is used as benign with probability Γ(1−y), as malicious with probability Γy, or skipped. With Γ = 0 nothing is learned. The first packet is assumed benign.");
  tag(s, "authors");
  [["p⁻ = Γ (1 − y_i)", "select as benign"], ["p⁺ = Γ · y_i", "select as malicious"], ["q = 1 − Γ", "do not use"]].forEach((r, i) => {
    const x = 0.5 + i * 3.05;
    eq(s, r[0], x, 1.5, 2.8, 0.9, 20);
    s.addText(r[1], { x, y: 2.5, w: 2.8, h: 0.35, fontSize: 13, color: H.muted, align: "center", margin: 0, isTextBox: true }); });
  bullets(s, ["Γ ∈ [0,1] is SSID's confidence in the IDS. Low trust means almost no packets are labelled.",
    "The first packet is assumed benign (p⁻ = 1), so the cold start lasts one packet.",
    "An auto-associative IDS learns only from benign samples."], { x: 0.5, y: 3.15, w: 9, h: 1.6 }); }

{ const s = slide("CONTENT", "Trust coefficient Γ = C_rep · C_gen",
  "C_rep: closed-form KL divergence between exponential TT/PL distributions of learned vs observed traffic, mapped by e^-D. C_gen: half data adequacy, half knowledge (EWMA of the training error).");
  tag(s, "authors");
  card(s, 0.5, 1.4, 4.35, 3.55, "Representativeness C_rep", "TT and PL are assumed exponential and independent.\n\nD_KL = log(λo/λl) − (λo − λl)/λo\n\nC_rep = ½[(λl/λo)·e^{1−λl/λo} + (μl/μo)·e^{1−μl/μo}]", H.amber);
  card(s, 5.15, 1.4, 4.35, 3.55, "Generalisation C_gen = ½Δ + ½κ", "Data adequacy:\nΔ = 1 − min(W / Σ|B_k|, 1)\n\nKnowledge:\nκ = 1 − Σ (½)^{l−k+1} E(k)\nκ ← ½ − ½(E(l) − κ)", H.amber); }

{ const s = slide("CONTENT", "Two phases decide when to learn",
  "Phase 0: update on every selected packet until trust reaches Θ. Phase ≥1: update only when trust has fallen, enough packets are collected, and no alarm is active. An alarm empties the batch so false negatives just before the alarm are not learned.");
  tag(s, "authors");
  card(s, 0.5, 1.4, 4.35, 2.6, "Initial learning  l = 0", "Update after every selected packet.\nEnd the phase once Γ ≥ Θ = 0.95   (14)", H.amber);
  card(s, 5.15, 1.4, 4.35, 2.6, "Online learning  l ≥ 1", "Collect selected packets in B_l.\nUpdate if Γ < Θ, |B_l| ≥ K = 100, and mean(y) ≤ γ = 0.25   (15)\nIf mean(y) > γ: empty B_l   (16)", H.amber);
  s.addText("Retraining happens only when needed: trust has dropped and the network looks clean.", { x: 0.5, y: 4.3, w: 9, h: 0.4, fontSize: 14, italic: true, color: H.slate, margin: 0, isTextBox: true }); }

// ======================================================================= Paper's evaluation
section("3 · The Paper's Evaluation", "Setup, metrics, reported results", "Member 3 starts here.");
{ const s = slide("CONTENT", "Experimental setup in the paper",
  "Datasets, tasks, baselines, metrics and parameters as reported.");
  tag(s, "authors");
  tbl(s, [["Item", "Setting"], ["Datasets", "Kitsune Mirai: 764k packets, 84% malicious · Kitsune SYN DoS · Bot-IoT DDoS HTTP/TCP/UDP, DoS HTTP"],
    ["Tasks", "Malicious-traffic detection (M=3) · compromised-device identification CDIS (M=6)"],
    ["Baselines", "AADRNN/MLP offline (83k benign pkts) and incremental (every 750 pkts) · KNN, Lasso · sequential CDIS"],
    ["Metrics", "ROC, accuracy, TPR, TNR · balanced accuracy for CDIS"], ["Parameters", "Θ = 0.95, I = 10, K = 100, γ = 0.25"]],
    0.5, 1.4, 9, [1.6, 7.4], 13); }

{ const s = slide("CONTENT", "Key results reported by the authors",
  "TPR above 0.995 at FPR around 1e-5. Learned from only 4,161 packets but competitive with offline training on 83k. CDIS improved by up to 18% median balanced accuracy.");
  tag(s, "authors");
  [["> 0.995", "TPR at FPR ≈ 10⁻⁵ (Kitsune-Mirai)"], ["4,161", "packets learned fully online, vs. 83,000 for the offline model"], ["+18%", "median balanced acc. for CDIS on Bot-IoT DDoS-TCP (+11% UDP)"]]
    .forEach((st, i) => { const x = 0.5 + i * 3.05;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.45, w: 2.8, h: 2.3, rectRadius: 0.1, fill: { color: H.light }, line: { color: H.light }, objectName: "stat" });
      s.addText(st[0], { x, y: 1.6, w: 2.8, h: 0.9, fontSize: 38, bold: true, color: H.amber, align: "center", fontFace: "Cambria", margin: 0, isTextBox: true });
      s.addText(st[1], { x: x + 0.2, y: 2.55, w: 2.4, h: 1.0, fontSize: 13, color: H.ink, align: "center", valign: "top", margin: 0, isTextBox: true }); });
  s.addText("Also reported: SSID clearly beats incremental learning, and SSID-MLP is second-best overall. Team note: the CDIS gains come mostly from TNR, and TPR is low.",
    { x: 0.5, y: 4.05, w: 9, h: 0.7, fontSize: 13, color: H.slate, margin: 0, isTextBox: true }); }

// ======================================================================= Critique
section("4 · Critical Assessment", "What holds up, and what does not", "Member 3 continues: the team's critique.");
{ const s = slide("CONTENT", "Strengths",
  "Acknowledge what the paper does well before critiquing it.");
  tag(s, "team");
  const c = [["Label-free & online", "No offline data, no human labels, a one-packet cold start"], ["Decides when to learn", "Trust-triggered updates replace a fixed schedule"],
    ["Model-agnostic", "Works with AADRNN, MLP and CDIS; we confirmed MLP"], ["Lightweight", "3–6 header metrics, O(1) statistics, output-layer-only updates"]];
  c.forEach((r, i) => { const x = 0.5 + (i % 2) * 4.6, y = 1.45 + Math.floor(i / 2) * 1.75;
    card(s, x, y, 4.4, 1.55, r[0], r[1], H.teal, H.light, 15); }); }

{ const s = slide("CONTENT", "Weakness 1: the self-labelling loop can be poisoned",
  "A slowly ramping attack stays under gamma, so it is accepted and learned, and 'normal' moves with the attack. Batch clearing never fires. Bootstrap: if the untrained output is 1, then E(0)=1, kappa=0, Delta=0, so Gamma=0 forever.");
  tag(s, "team");
  card(s, 0.5, 1.4, 4.35, 3.55, "Boiling-frog attack", "Training labels come from the IDS itself.\n\nRaise the attack rate slowly → each batch stays just under γ → it is learned → the profile of \"normal\" follows the attack.\n\nThe batch-clearing rule (16) never fires. The paper does not test this.", H.red, "FEF2F2");
  card(s, 5.15, 1.4, 4.35, 3.55, "Bootstrap deadlock", "At l = 0, Δ = 0, so C_gen = ¼(1 − E(0)).\n\nIf the untrained IDS outputs y = 1, then E(0) = 1 → κ = 0 → Γ = 0 → q = 1: nothing is ever selected.\n\nThe first packet must also be benign: an infected network at deployment is learned as normal.", H.red, "FEF2F2"); }

{ const s = slide("CONTENT", "Weakness 2: mathematical issues we found",
  "Walk through each equation issue.");
  tag(s, "team");
  tbl(s, [["Where", "Issue", "Fix"], ["Eq. (35)", "Weights sum to 1 − 2^{−(l+1)}: κ is biased upward (κ = 1 − E/2 at l = 0)", "Divide by Σw (bias-corrected)"],
    ["Eq. (38)", "Sign typo: “+ΣE” should be “1 − ΣE” (inconsistent with eq. 37)", "[2 − min(·) − ΣE]/2"],
    ["Eq. (10)", "O₀ uses X̂_H, but (11)–(12) use X̂_{H−1}; singular with < M+1 samples", "Use X̂_{H−1} + ridge"],
    ["Eq. (28)", "Labelled D^PL but gives D^TT", "Relabel"], ["Eqs. (15)/(16)", "Window covers I packets in (15) but I+1 in (16)", "Use the same window"],
    ["Eq. (4)", "Discriminant negative for small Λ; no domain given", "Clip to 0 / state domain"]],
    0.5, 1.4, 9, [1.3, 5.2, 2.5], 12); }

{ const s = slide("CONTENT", "Weakness 3: assumptions and evaluation gaps",
  "Assumptions on the left, evaluation gaps on the right.");
  tag(s, "team");
  s.addText("Restrictive assumptions", { x: 0.5, y: 1.4, w: 4.3, h: 0.35, fontSize: 15, bold: true, color: H.teal, margin: 0, isTextBox: true });
  bullets(s, ["Exponential TT/PL, while real packet lengths are bimodal; C_rep compares means only",
    "Cumulative statistics react slowly to drift", "\"Observed normal\" comes from the IDS's own decisions, which is circular",
    "Fixed γ = 0.25 depends on the metric scale"], { x: 0.5, y: 1.85, w: 4.3, h: 3.1, fontSize: 13 });
  s.addText("Evaluation gaps", { x: 5.2, y: 1.4, w: 4.3, h: 0.35, fontSize: 15, bold: true, color: H.teal, margin: 0, isTextBox: true });
  bullets(s, ["One detection trace, 84% malicious, so accuracy is inflated", "No variance over runs; no sensitivity analysis on Θ or γ",
    "No KitNET baseline; no runtime or memory figures", "Benign drift and adversarial attacks are never tested",
    "Per-packet labels on window-aggregated metrics"], { x: 5.2, y: 1.85, w: 4.3, h: 3.1, fontSize: 13 }); }

// ======================================================================= Ours
section("5 · SSID+ and Experimental Validation", "Our five fixes, implementation and results", "Member 4 starts here.");
{ const s = slide("CONTENT", "SSID+: five label-free changes",
  "Each change maps to a weakness. Gate and adaptive gamma control what is learned; JS, unbiased kappa and forgetting control how fast it adapts.");
  tag(s, "team");
  const c = [["Windowed Jensen–Shannon C_rep", "Distribution-free, bounded in [0,1], follows drift", "exponential / cumulative"],
    ["Bias-corrected κ", "κ = 1 − ΣwE/Σw", "κ inflated early"],
    ["Confidence gate", "Accept as benign only if y ≤ min(γ/2, μ + 3σ)", "self-poisoning"],
    ["Adaptive threshold", "γ_t = clip(μ + 6σ, 0.03, γ) from accepted outputs", "scale-dependent γ"],
    ["Forgetting OS-ELM", "λ_f = 0.995 so old traffic fades", "slow adaptation"]];
  c.forEach((r, i) => { const y = 1.38 + i * 0.75; num(s, 0.5, y, i + 1);
    s.addText(r[0], { x: 1.05, y: y - 0.03, w: 3.2, h: 0.48, fontSize: 14, bold: true, color: H.ink, margin: 0, valign: "middle", isTextBox: true });
    s.addText(r[1], { x: 4.25, y: y - 0.03, w: 3.4, h: 0.48, fontSize: 12, color: H.slate, margin: 0, valign: "middle", isTextBox: true });
    s.addText("fixes: " + r[2], { x: 7.7, y: y - 0.03, w: 1.8, h: 0.48, fontSize: 11, italic: true, color: H.teal, margin: 0, valign: "middle", isTextBox: true }); }); }

{ const s = slide("CONTENT", "Implementation",
  "Show the code in the editor. Every line of the SSID loop is annotated with its equation number. List the implementation choices the paper does not specify.");
  tag(s, "team");
  tbl(s, [["File", "What it does"], ["ssid/traffic.py", "Scenarios, CSV loader, causal M=3 metrics"],
    ["ssid/models.py", "ζ (eq. 4), FISTA (7), AADRNN + OS-ELM (10–12), MLP-AE"], ["ssid/framework.py", "SSID loop (13–38), SSID+ switches, baselines"],
    ["run_experiments.py", "Seeds × scenarios × methods, ablation, sensitivity"], ["pcap_to_csv.py", "Run on the real Kitsune / Bot-IoT pcaps"]],
    0.5, 1.4, 5.3, [1.75, 3.55], 12);
  card(s, 6.1, 1.4, 3.4, 3.55, "Choices the paper leaves open", "• Ridge 10⁻³ in O₀\n• Frozen input scaling (otherwise eq. 7 collapses onto the bias)\n• Untrained y = 0.5 (y = 1 deadlocks)\n• Batch capped at 5,000\n• Python 3 · NumPy · scikit-learn", H.teal, "ECFDF5"); }

{ const s = slide("CONTENT", "Experimental setup",
  "Synthetic, reproducible traces, because Kitsune/Bot-IoT need registration. Three scenarios, five seeds, the paper's parameters. FPR is measured outside attack windows.");
  tag(s, "team");
  [["mirai", "Stationary benign traffic, then an abrupt flood at 60 pkt/s (close to the paper's setting)"], ["mirai_drift", "4 new devices join one by one (benign drift), then the flood"],
    ["slow_ramp", "Drift, then an attack that ramps 0 → 60 pkt/s over 900 s (adversarial)"]].forEach((r, i) => {
    card(s, 0.5 + i * 3.05, 1.4, 2.85, 2.0, r[0], r[1], H.teal); });
  s.addText("Baselines: Offline-AADRNN / KNN / IForest (5,000 oracle-labelled packets) · Incremental-AADRNN (750) · SSID-AADRNN · SSID-MLP · SSID+.  Metrics: TPR, TNR, balanced accuracy, AUC, µs per packet.  5 seeds, about 60–90k packets each.",
    { x: 0.5, y: 3.65, w: 9, h: 1.0, fontSize: 13, color: H.slate, margin: 0, isTextBox: true }); }

{ const s = slide("CONTENT", "Results: balanced accuracy across scenarios",
  "Read the numbers. SSID reproduces the paper on mirai and drift. On slow_ramp it collapses to 0.5. SSID+ stays at 0.99. The offline detectors fail under drift.");
  tag(s, "team");
  img(s, "balacc_comparison.png", 0.4, 1.35, 9.2, 3.75, "Balanced accuracy bar charts for three scenarios"); }

{ const s = slide("CONTENT", "Why SSID fails on the slow ramp, and SSID+ does not",
  "Top: the paper's SSID output rises with the attack but stays under 0.25; trust dips, an update fires around 2,500 s, and the attack becomes 'normal'. Bottom: SSID+'s adaptive threshold (about 0.09) fires early, so attack batches are cleared and never learned.");
  tag(s, "team");
  img(s, "timeline_slow_ramp.png", 0.4, 1.3, 6.2, 3.6, "Slow-ramp timeline");
  [["TPR " + f3(g("slow_ramp", "SSID-AADRNN (paper)", "TPR")), "paper's SSID: attack learned as normal", H.red], ["TPR " + f3(g("slow_ramp", "SSID+ (ours)", "TPR")), "SSID+: attack still detected", H.teal],
    ["TNR 0.9999", "same false-alarm rate for both", H.slate]].forEach((r, i) => {
    s.addText(r[0], { x: 6.85, y: 1.4 + i * 1.2, w: 2.7, h: 0.5, fontSize: 24, bold: true, color: r[2], fontFace: "Cambria", margin: 0, isTextBox: true });
    s.addText(r[1], { x: 6.85, y: 1.9 + i * 1.2, w: 2.7, h: 0.5, fontSize: 12, color: H.ink, margin: 0, isTextBox: true }); }); }

{ const s = slide("CONTENT", "Ablation: which component stops self-poisoning?",
  "Adaptive gamma does most of the work. The gate helps partly. JS and forgetting alone do not help; they speed adaptation. The full combination is best and has the lowest variance.");
  tag(s, "team");
  img(s, "ablation_slow_ramp.png", 0.4, 1.35, 6.4, 3.7, "Ablation bar chart: TPR on slow-ramp attack");
  card(s, 7.05, 1.35, 2.45, 3.7, "Reading", "How fast it learns: JS, κ and forgetting.\n\nWhat it learns: the gate and adaptive γ.\n\nYou need the second group to resist poisoning.", H.teal, "ECFDF5"); }

{ const s = slide("CONTENT", "Sensitivity and cost",
  "Theta and gamma sensitivity for the paper's SSID: gamma = 0.4 breaks detection, and moving theta from 0.95 costs about 10 points. Cost: SSID+ takes 40–100 µs per packet in Python, still more than 10k packets/s.");
  tag(s, "team");
  img(s, "sensitivity_theta_gamma.png", 0.4, 1.3, 4.4, 3.65, "Theta-gamma sensitivity heatmap");
  card(s, 5.1, 1.35, 4.4, 1.65, "Sensitivity (paper's SSID)", "Balanced accuracy ranges 0.50–0.998. γ = 0.40 breaks detection completely. The \"no tuning\" claim does not hold.", H.teal);
  card(s, 5.1, 3.2, 4.4, 1.75, "Cost per packet (Python)", "SSID " + g("mirai", "SSID-AADRNN (paper)", "us_per_pkt").toFixed(0) + "–" + g("slow_ramp", "SSID-AADRNN (paper)", "us_per_pkt").toFixed(0) +
    " µs · SSID+ " + g("mirai", "SSID+ (ours)", "us_per_pkt").toFixed(0) + "–" + g("slow_ramp", "SSID+ (ours)", "us_per_pkt").toFixed(0) + " µs. That is still more than 10k packets/s on one core.", H.teal); }

{ const s = slide("CONTENT", "Conclusion",
  "Wrap up. State the takeaways, the limits of our study (synthetic traces), and future work.");
  card(s, 0.5, 1.2, 4.35, 3.75, "Authors' claim: holds", "On abrupt attacks and on gradual drift, SSID trains an IDS fully online with no labels and matches offline training. It also handles benign drift, which we tested and the paper did not.", H.amber, "FFFBEB", 16);
  card(s, 5.15, 1.2, 4.35, 3.75, "Team's findings", "• A slow-ramp attack poisons SSID (TPR ≈ 0)\n• Bootstrap deadlock, κ bias, equation typos\n• SSID+ restores TPR to 0.985\n• Next: test on the real datasets, add change detection and anchor memory, federated SSID", H.teal, "ECFDF5", 16); }

{ const s = slide("CONTENT", "References",
  "Thank the audience and invite questions.");
  bullets(s, ["[1] M. Nakıp, E. Gelenbe, “Online Self-Supervised Deep Learning for Intrusion Detection Systems,” IEEE TIFS 19, 2024",
    "[17] Y. Mirsky et al., “Kitsune: An ensemble of autoencoders for online NIDS,” NDSS 2018",
    "[18] N. Koroniotis et al., “Bot-IoT dataset,” FGCS 100, 2019",
    "[58] A. Beck, M. Teboulle, “FISTA,” SIAM J. Imaging Sci., 2009 · [59] N.-Y. Liang et al., “OS-ELM,” IEEE TNN, 2006",
    "J. Lin, “Divergence measures based on Shannon entropy,” IEEE TIT 1991 (JS) · E. Arazo et al., “Pseudo-labeling and confirmation bias,” IJCNN 2020",
    "Figures on slides 9–10: team's re-drawings of Figs. 1–3 in [1]. All result charts are the team's own."], { x: 0.5, y: 1.2, w: 9, h: 3.8, fontSize: 12 }); }

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
