# MetaAudit — OSF Pre-Registration

## Study Information

**Title:** MetaAudit: A Computational Full-Spectrum Audit of Cochrane Meta-Analyses

**Authors:** Mahmood Ahmad (Royal Free Hospital, London, UK)
**ORCID:** 0009-0003-7781-4478

**Description:** A computational meta-epidemiological study applying 11 automated flaw detectors to all meta-analyses in the Pairwise70 dataset (501 Cochrane systematic reviews, ~50,000 RCTs). This is the first study to simultaneously audit statistical, bias, integrity, and interpretation flaws across a large corpus of meta-analyses using study-level recomputation.

**Hypotheses:**
1. The majority (>50%) of Cochrane meta-analyses will have at least one detectable methodological flaw.
2. Publication bias will be the most prevalent single flaw category.
3. Flaws will co-occur non-randomly — reviews with one flaw will be more likely to have others.

## Design Plan

**Study type:** Meta-epidemiological study (observational, cross-sectional audit)

**Pre-registration date:** 2026-03-28

**Data collection has already begun:** Yes. The Pairwise70 dataset is pre-existing and publicly documented. No new data collection is involved.

## Sampling Plan

**Existing data:** The Pairwise70 dataset contains 501 Cochrane systematic reviews with study-level data for all included RCTs. This is a census, not a sample — all available reviews in the dataset are included.

**Sample size:** 6,229 meta-analyses from 501 reviews (~50,000 individual RCTs).

**No stopping rule:** All available data are analysed.

## Variables

**Independent variables (detectors):**
1. Prediction Gap — 95% PI includes null despite significant CI
2. Model Misspecification — I² > 50% suggesting RE model needed; OR used for common outcomes
3. Fragility (MAFI) — Minimum event changes to lose significance
4. Underpowered — k < 3 with significant result; total N below OIS
5. Publication Bias — Egger's test + Begg's rank test + trim-and-fill (k ≥ 10 required)
6. Small-Study Effects — Precision-effect regression + Spearman |effect|~variance correlation
7. Excess Significance — Ioannidis-Trikalinos test (O/E > 1.5, p < 0.10)
8. Data Integrity — Impossible values, GRIM consistency, duplicate patterns
9. Study Overlap — Cross-review study sharing > 30%
10. Overclaiming — Significant effect below MCID (log(1.25) for OR, 0.2 for SMD)
11. Certainty-Outcome Mismatch — GRADE rating inconsistent with automated severity (if GRADE data available)

**Dependent variable:** Severity classification per meta-analysis per detector: PASS, WARN, FAIL, or CRITICAL.

## Analysis Plan

**Statistical models:**
- REML random-effects models with Hartung-Knapp-Sidik-Jonkman adjustment
- 95% prediction intervals (Higgins-Thompson-Spiegelhalter)
- Continuity correction (0.5) for zero cells in binary outcomes

**Primary outcomes:**
1. Prevalence of each flaw category (proportion of MAs with FAIL or CRITICAL)
2. Overall proportion of MAs with ≥1 FAIL
3. Overall proportion of MAs with ≥3 FAILs

**Secondary outcomes:**
1. Pairwise co-occurrence rates (phi coefficients between all detector pairs)
2. Severity score distribution (weighted: WARN=1, FAIL=2, CRITICAL=3)
3. Top 10 most-flawed reviews (case studies)

**Exploratory outcomes:**
1. Specialty-stratified flaw profiles (using Cochrane review group as proxy)
2. Temporal trends (comparing older vs newer reviews)

**Inference criteria:**
- Detector thresholds are pre-specified (see Variables section above)
- No multiple testing adjustment — each detector is an independent diagnostic
- Confidence intervals for prevalence computed using Wilson method

**Sensitivity analyses:**
1. Threshold sensitivity: re-run with ±10% shifts on all detector thresholds
2. Exclude reviews with k < 5 studies
3. Binary outcomes only (exclude continuous and GIV)
4. Compare REML tau² against DerSimonian-Laird to assess estimator sensitivity

**Data exclusion:** Meta-analyses with k < 2 studies are excluded from pooling. Detectors requiring k ≥ 10 (publication bias, small-study effects) report "insufficient data" rather than PASS for smaller MAs.

## Other

**Code availability:** All code is open-source at https://github.com/mahmood726-cyber/metaaudit

**Dashboard:** Interactive results at https://mahmood726-cyber.github.io/metaaudit/dashboard/index.html

**Reproducibility:** Results are fully deterministic given the Pairwise70 dataset and the MetaAudit codebase at the tagged release.

---

**AI Disclosure Statement**

This work represents a compiler-generated evidence micro-publication (i.e., a structured, pipeline-based synthesis output). AI is used as a constrained synthesis engine operating on structured inputs and predefined rules, rather than as an autonomous author. Deterministic components of the pipeline, together with versioned, reproducible evidence capsules (TruthCert), are designed to support transparent and auditable outputs. All results and text were reviewed and verified by the author, who takes full responsibility for the content. The workflow operationalises key transparency and reporting principles consistent with CONSORT-AI/SPIRIT-AI, including explicit input specification, predefined schemas, logged human-AI interaction, and reproducible outputs.
