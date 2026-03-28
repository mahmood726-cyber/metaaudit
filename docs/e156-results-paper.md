# MetaAudit: E156 Results Paper

**Background:** Meta-analyses are the highest tier of evidence, yet no study has computationally audited their quality at scale. Prior meta-epidemiological studies examined only one or two flaws across fewer than 300 reviews using manual methods.

**Objective:** To quantify the prevalence and co-occurrence of methodological flaws across 6,229 Cochrane meta-analyses from 501 systematic reviews using eleven automated detectors.

**Methods:** Study-level data from Pairwise70 were reanalysed using REML with Hartung-Knapp-Sidik-Jonkman adjustment. Eleven detectors assessed prediction gaps, model misspecification, fragility, underpowering, publication bias, small-study effects, excess significance, data integrity, study overlap, overclaiming, and certainty mismatch.

**Results:** Overall, 29.5% of meta-analyses failed at least one detector and 3.1% failed three or more. Publication bias was most prevalent (37.2%), followed by model misspecification (15.1%) and prediction gap (11.2%). Model misspecification and excess significance co-occurred strongly (phi=0.384).

**Conclusion:** Nearly one-third of Cochrane meta-analyses exhibit computationally detectable methodological flaws, with publication bias and model misspecification dominant. Automated quality auditing should complement peer review.

---

**References**
- Protocol: https://github.com/mahmood726-cyber/metaaudit/releases/tag/v0.1.0-preregistration
- Dashboard: https://mahmood726-cyber.github.io/metaaudit/dashboard/index.html
- Code: https://github.com/mahmood726-cyber/metaaudit
- WebR Verification: https://mahmood726-cyber.github.io/metaaudit/dashboard/webr-verify.html

---

**AI Disclosure Statement**

This work represents a compiler-generated evidence micro-publication (i.e., a structured, pipeline-based synthesis output). AI is used as a constrained synthesis engine operating on structured inputs and predefined rules, rather than as an autonomous author. Deterministic components of the pipeline, together with versioned, reproducible evidence capsules (TruthCert), are designed to support transparent and auditable outputs. All results and text were reviewed and verified by the author, who takes full responsibility for the content. The workflow operationalises key transparency and reporting principles consistent with CONSORT-AI/SPIRIT-AI, including explicit input specification, predefined schemas, logged human–AI interaction, and reproducible outputs.
