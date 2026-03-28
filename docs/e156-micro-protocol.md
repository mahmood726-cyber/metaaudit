# MetaAudit: E156 Micro-Protocol

**Background:** Meta-analyses underpin clinical guidelines, yet systematic flaws — including underpowering, model misspecification, and overclaiming — remain unquantified at scale across Cochrane evidence syntheses globally.

**Objective:** To estimate the prevalence and co-occurrence of eleven computational flaw categories across 6,229 Cochrane meta-analyses derived from 501 systematic reviews.

**Methods:** We reanalyse study-level data from the Pairwise70 dataset (~50,000 RCTs) using REML random-effects models with Hartung-Knapp-Sidik-Jonkman correction. Eleven automated detectors are applied: prediction gaps, model misspecification, fragility index, underpowering, publication bias, small-study effects, excess significance, data integrity failures, study overlap, overclaiming versus MCID, and certainty-outcome mismatch. Each meta-analysis receives a severity classification of PASS, WARN, FAIL, or CRITICAL.

**Analysis Plan:** Primary outcome is the prevalence of each flaw category; secondary outcomes include pairwise co-occurrence rates, specialty-stratified rates, and temporal trends spanning 2000 to 2024. All analyses are pre-specified and fully reproducible via versioned TruthCert capsules registered on OSF.

**Expected Output:** Flaw prevalence estimates with 95% confidence intervals, a co-occurrence network, and an openly accessible severity dashboard for researchers.

---

**References**
- Protocol: https://github.com/mahmood726-cyber/metaaudit/releases/tag/v0.1.0-preregistration
- Dashboard: https://mahmood726-cyber.github.io/metaaudit/dashboard/index.html
- Code: https://github.com/mahmood726-cyber/metaaudit

---

**AI Disclosure Statement**

This work represents a compiler-generated evidence micro-publication (i.e., a structured, pipeline-based synthesis output). AI is used as a constrained synthesis engine operating on structured inputs and predefined rules, rather than as an autonomous author. Deterministic components of the pipeline, together with versioned, reproducible evidence capsules (TruthCert), are designed to support transparent and auditable outputs. All results and text were reviewed and verified by the author, who takes full responsibility for the content. The workflow operationalises key transparency and reporting principles consistent with CONSORT-AI/SPIRIT-AI, including explicit input specification, predefined schemas, logged human–AI interaction, and reproducible outputs.
