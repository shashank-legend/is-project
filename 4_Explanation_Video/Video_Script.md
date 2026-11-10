# Explanation Video — Script and Recording Plan

**Paper:** M. Nakıp and E. Gelenbe, "Online Self-Supervised Deep Learning for Intrusion Detection Systems," *IEEE Trans. Information Forensics and Security*, vol. 19, pp. 5668–5683, 2024. DOI: 10.1109/TIFS.2024.3402148

**Length:** about 18–22 minutes in total, roughly 5 minutes per member.
**How to record:** Use Zoom or Google Meet, share the PPT and turn on every camera. Each member's **name and face must be visible** while they speak. Rename yourself in Zoom to "Full Name – Roll No." so the name shows on screen.
**Split:** The plan assumes a team of four. With three members, merge Parts C and D. Replace "Member 1–4" with your real names.

---

## Part A — Member 1: Problem, motivation, related work (slides 1–6, ~5 min)

1. **Introduction (20 s).** "Hi, I'm ___. Our team analysed the TIFS 2024 paper by Nakıp and Gelenbe on *online self-supervised deep learning for intrusion detection*. I'll cover the problem and motivation, ___ will explain the method, ___ the results and our critique, and ___ our implementation and improvements."
2. **Problem (60 s).** Explain Mirai-style botnets in IoT: compromised devices launch DDoS. IoT devices are cheap and numerous, so the IDS has to be lightweight. Anomaly-based IDSs can catch zero-day attacks, but they learn what "normal" looks like. When normal traffic drifts, for example when new devices join, false alarms go up.
3. **Why online learning is hard (60 s).** Explain the paper's two obstacles: (i) labelled data is rarely available for each deployment, and (ii) choosing *when* to retrain is hard. Retraining too often wastes compute. Retraining too rarely means the model goes stale.
4. **Related work (60 s).** Explain that existing self-supervised IDSs (BYOL, GAN-based, GNN Anomal-E, LSTM-AE and others) still need offline data or an extra generative/contrastive model. SSID claims three things: no offline data, no generative model, and fully online learning on each node.
5. **Contributions (40 s).** Read the contributions slide: the SSID framework, the trust coefficient Γ, self-supervised packet selection, trust-triggered updates, and an evaluation on Kitsune and Bot-IoT.

## Part B — Member 2: System model and methodology (slides 7–12, ~6 min)

1. **IDS structure (60 s).** Show the AADRNN diagram. It takes M=3 header-only metrics, reconstructs "expected benign" metrics, and sets y = mean |x − x̂| (eq. 5). For compromised-device identification it uses 6 metrics and a max-deviation decision instead (eq. 6).
2. **DRNN learning (60 s).** The hidden layers are trained with non-negative L1 least squares solved by FISTA (eq. 7). The output layer is updated online with OS-ELM recursive least squares (eqs. 10–12). Point out that only the output layer is updated online.
3. **SSID loop (90 s).** Use the architecture figure. Detection runs unchanged. In parallel, each packet is selected as benign with probability Γ(1−y), as malicious with probability Γy, or skipped with probability 1−Γ (eqs. 17–20).
4. **Trust coefficient (90 s).** Γ = C_rep · C_gen. C_rep compares the traffic the model has learned with the traffic it observes. It assumes inter-arrival times and packet lengths are exponential, uses the closed-form KL divergence, and maps it with e^−D (eqs. 22–32). C_gen = ½Δ + ½κ, where Δ is data adequacy relative to the number of parameters W and κ is an exponentially weighted moving average (EWMA) of the training error (eqs. 33–38).
5. **Phases (60 s).** In phase l=0, the model updates on every selected packet until Γ ≥ Θ = 0.95. In phases l≥1, it updates only when Γ < Θ, the batch holds at least K = 100 packets, and no alarm is active. When an alarm fires, the batch is emptied (eqs. 14–16).

## Part C — Member 3: Results and critical assessment (slides 13–19, ~6 min)

1. **Paper's setup (45 s).** Kitsune Mirai has 764,137 packets, of which 642,516 are malicious. Bot-IoT covers DDoS/DoS over HTTP, TCP and UDP. The parameters are Θ=0.95, I=10, K=100, γ=0.25. Baselines are offline and incremental AADRNN, MLP, KNN and Lasso.
2. **Paper's results (60 s).** TPR is above 0.995 at an FPR of about 10⁻⁵. SSID learned from only 4,161 packets yet competes with an offline model trained on 83k packets. For SSID-CDIS, median balanced accuracy rises by 18% on DDoS-TCP and 11% on DDoS-UDP.
3. **Critique, in our own words (3 min).** Go through the critique slides:
   - **Self-poisoning:** the IDS labels its own training data, so a slowly ramping attack can be learned as normal. The paper never tests this. Our experiment shows TPR falling to 0.
   - **Bootstrap fragility:** if the first output is E(0)=1, then κ=0 and Δ=0, so Γ=0 forever and learning never starts. The first packet must also be benign.
   - **Mathematical issues:** κ is biased upward because the weights in eq. (35) sum to less than 1. Eq. (38) has a sign typo. Eq. (10) uses X_H where it should use X_{H−1}. The label on eq. (28) is wrong.
   - **Modelling assumptions:** packet length is assumed exponential, but real packet lengths are bimodal. C_rep compares only means and is cumulative, so it reacts slowly to drift.
   - **Evaluation gaps:** the Mirai data is 84% malicious, so accuracy is inflated. KitNET, which is Kitsune's own online detector, is not compared. There is no variance over runs, no latency or memory measurement, and no sensitivity analysis on Θ and γ, even though γ depends on the metric scale.
   - **Labelling of aggregate metrics:** benign packets inside an attack window have attack-like metrics.

## Part D — Member 4: Implementation, improvements, results, conclusion (slides 20–27, ~6 min)

1. **Implementation (90 s).** Show `3_Source_Code/` in your editor. Walk through `ssid/models.py` (ζ activation, FISTA, OS-ELM), `ssid/framework.py` (the `SSID.run` loop, with each equation number marked in comments) and `ssid/traffic.py` (scenarios and metrics). Explain the implementation choices: frozen input scaling, standardisation of the hidden layer, and ridge regularisation in O₀.
2. **Live run (45 s).** Run `python run_experiments.py --quick` and show the console output and the `results/figures` folder. Note that this runs on synthetic data because Kitsune requires a Kaggle download. `pcap_to_csv.py` converts the real pcap into the same CSV format.
3. **SSID+ (90 s).** Present the five changes and what each fixes: JS representativeness, unbiased κ, the confidence gate, adaptive γ, and the forgetting factor.
4. **Results (90 s).** Show the timeline figure for slow_ramp, the balanced-accuracy bars and the ablation. Read the numbers off the slides. Make clear that the paper's SSID reproduces well on an abrupt Mirai attack and on gradual drift, and that SSID+ keeps that performance while resisting the slow-ramp poisoning attack. State the costs: SSID+ takes more time per packet, and a gate that is too strict cannot adapt to an abrupt benign drift.
5. **Conclusion (30 s).** Give the takeaways and future work: run on the real datasets, federated SSID, and adversarial evaluation. Thank the audience.

---

### Likely viva questions (prepare answers)

- *Why is Γ a product rather than a sum?* If either factor is low, trust should be low. A product works like a soft AND.
- *Why does the AADRNN learn only benign traffic?* It is an anomaly detector. Malicious samples (p⁺) are not used to train an auto-associative model.
- *Why does the slow-ramp attack beat SSID?* Each batch is only slightly more anomalous than the last. Every batch stays below γ, so it is accepted and learned, and the "normal" profile moves along with the attack.
- *How does the gate stop that?* Packets are accepted only if y ≤ min(γ/2, μ + 3σ), where μ and σ come from packets already accepted. A gradual drift moves μ slowly, while the attack's y grows faster than that.
- *What does SSID+ cost?* About 6× more µs per packet in our Python implementation, mainly from the JS histograms. That is still far below the inter-arrival time.
