**Strong, focused, and conference-ready with targeted polishing.** This is already one of the cleaner experiment designs I've seen for a short NLP paper (8–10 pages, one clear figure). It has a crisp research question, tight scope, honest baselines, reusable artifacts, and a practical SPRINT tie-in that gives it impact. The v3.1 convergence shows good iteration.

### Major Strengths
- **Clarity and self-containment** — The one-sentence RQ, two explicit axes, and single-figure plan make it very readable. The task definition (§3) is excellent: precise, linguistically grounded (Katka sign-off), and operationalized with edge-case handling. This is publishable as-is for the methodology section.
- **Honest baselines and gold** — Measuring the parser arm *on the same unfiltered data* against human gold (including the interpretation gap) is the right way to do it. No overclaiming. The IAA setup (linguist × trained non-linguist) is pragmatic and relevant to real deployment.
- **Practical relevance** — The SPRINT/per-rule-prose framing is a genuine contribution. Many papers ignore the "how do non-experts maintain this?" angle; you address it directly.
- **Efficiency** — Minimal grid (no sweeps), resumable harness, cost awareness, and anti-caching protocol show maturity. The deliverables list is perfect for a short paper.
- **Scientific grounding** — Clear link to exp_01, related work threads referenced, hypotheses testable from one figure.

### Weaknesses / Risks (mostly fixable)
1. **Scope Creep Risk in §3/K6** — The provisional shared-subject coordination decision (K6) is flagged, which is good, but if Katka changes it post-experiment it could force re-annotation or re-scoring. **Fix**: Run a sensitivity analysis on the gold-200 (report numbers under both conventions) or get final sign-off *before* full runs. Mention in the paper as a minor robustness check.

2. **Gold Size and Power** — 200 sentences (140 random + 60 targeted) is reasonable for a short paper but borderline for strong claims on rare phenomena (copular, aby-clauses, etc.). The targeted set helps, but headline metrics on the random 140 only is the clean story. **Suggestion**: Explicitly power the main comparison (e.g., detectable difference of 5–7 pts at α=0.05) and note the targeted set is for diagnosis only.

3. **Formulation Axis** — R1 (production) vs. R2 (procedural) is good, but the paper should be crystal-clear that R2 bundles *both* better definition *and* scaffolding. This is fine if you frame it as "best realistic lawyer rule vs. best procedural rule," but avoid implying it's a pure scaffold ablation. Add one sentence in §5.2 referencing the literature on their interaction.

4. **Parser Baseline Interpretation** — §3.6 is excellent, but readers might still wonder "is the parser cheating?" Strengthen the takeaway: "The parser arm's error includes both genuine parse failures *and* any systematic mismatch between UD extraction and the linguistic definition — both are part of the real engineering cost of the deterministic path."

5. **Minor Presentation**:
   - Threshold semantics (§3.5) — Make the off-by-one history a footnote; lead with the final T=6 aligned to PONK/production.
   - Cost/latency — Report as ranges or per-1k-sentence normalized; frontier+reasoning will dominate and should be called out.
   - Open items (§11) — Move resolved ones to a short "Decisions" paragraph in §3 or §5; keep only true opens.

### Suggestions to Strengthen for Conference
- **The Figure** — Make it the hero: verdict accuracy (F1 or accuracy) on y-axis, capability axis on x (with labels like "open 30B / open 70B / frontier / frontier+reasoning"). Two lines (R1/R2), dashed horizontal parser baseline + CI. Add a small table inset or second panel for decomposition (identification vs. counting error) to support H4 without extra figures. This single visualization can carry most claims.
- **Error Analysis** — Plan a short qualitative section on 20–30 residual errors (categorized by phenomenon). This often makes short papers memorable.
- **Related Work** — Keep tight: exp_01, SPRINT context, LLM parsing papers (step-by-step, self-correction, procedural prompting), and Czech readability work (LiFR/PONK). Cite the "LLMs as rule engines" thread explicitly.
- **Limitations** — Add a short paragraph: sentence segmentation held fixed, gold size, no fine-tuning/tool-use, Czech-specific (but generalizable framing).
- **Reproducibility** — Commit prompts, extraction code, gold (anonymized if needed), and harness. Offer the R2 rule as a SPRINT-ready artifact.
- **Title/Abstract Angle** — Something like: "Can LLMs Replace Parser Pipelines for Syntactic Metrics in Legal Text? A Pure-Prompt Evaluation on Czech Subject–Predicate Distance." Emphasize the per-rule-prose economics.

**Overall Viability**: This is **ready for submission** after the Katka sign-off loop and one polishing pass. It tells a complete, self-contained story with real practical value. The hybrid angle (parser vs. pure LLM) and the counting-vs-identification decomposition are the novel bits that reviewers will like. For a short conference paper it hits the sweet spot: focused question, clean design, reusable outputs.

If you want, I can:
- Draft the abstract/intro skeleton.
- Suggest specific prompts for R1/R2.
- Help formalize the extraction code or scoring script.
- Brainstorm the error inventory categories.

This is excellent work — it feels like the right next step after exp_01. What's your priority for the next iteration?