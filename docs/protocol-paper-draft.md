# MetaAudit: Protocol for a Computational Full-Spectrum Audit of Cochrane Meta-Analyses

**Author:** Mahmood Ahmad, Royal Free Hospital, London, United Kingdom
**Email:** mahmood.ahmad2@nhs.net
**ORCID:** 0009-0003-7781-4478

---

## Abstract

**Background:** Meta-analyses are the cornerstone of evidence-based medicine, yet emerging evidence suggests they harbour systematic methodological flaws — including underpowering, heterogeneity mismanagement, fragility, and overclaiming — that may undermine the reliability of clinical guidelines. No study has simultaneously audited the full spectrum of these flaws at scale using recomputed, study-level data.

**Objective:** To estimate the prevalence and co-occurrence of eleven pre-specified computational flaw categories across 4,424 Cochrane meta-analyses drawn from 501 systematic reviews.

**Methods:** We reanalyse study-level data from the Pairwise70 dataset (~50,000 RCTs) using REML random-effects models with Hartung-Knapp-Sidik-Jonkman (HKSJ) correction. Eleven automated detectors assess: prediction intervals versus confidence intervals (prediction gap), model misspecification (fixed vs. random effects), fragility (Meta-Analysis Fragility Index, MAFI), statistical underpowering, publication bias (Egger, Begg, trim-and-fill), small-study effects (Peters test, Spearman rank), excess significance (Ioannidis-Trikalinos), data integrity (GRIM test), study overlap across reviews, overclaiming relative to the Minimal Clinically Important Difference (MCID), and certainty-outcome mismatch between GRADE ratings and automated severity. Each meta-analysis is assigned a severity classification: PASS, WARN, FAIL, or CRITICAL.

**Analysis Plan:** The primary outcome is the prevalence of each flaw category with 95% confidence intervals. Secondary outcomes include pairwise flaw co-occurrence rates, specialty-stratified prevalence, and temporal trends from 2000 to 2024. All analyses are pre-specified and reproducible via versioned TruthCert capsules. OSF pre-registration is planned prior to analysis.

**Expected Output:** Flaw prevalence estimates for all eleven categories, a co-occurrence heatmap and network, specialty-stratified breakdowns, a temporal trend analysis, and an openly accessible severity dashboard. The dataset and code will be released under open licences.

---

## 1. Introduction

### 1.1 The Centrality of Meta-Analysis in Clinical Decision-Making

Meta-analysis is the dominant tool for synthesising clinical trial evidence. Its outputs directly inform clinical practice guidelines from bodies including the World Health Organization, NICE, and international cardiology and oncology societies. For this reason, the integrity of individual meta-analyses has outsized importance: a flawed synthesis, once embedded in a guideline, can propagate to millions of clinical decisions before correction reaches practice.

### 1.2 The Known Problem: Methodological Flaws at Scale

A growing body of methodological research has documented specific failure modes in published meta-analyses. Ioannidis and Trikalinos (2007) demonstrated that excess significance — the observation of more statistically significant primary studies than expected under the pooled effect — is widespread and may reflect selective reporting or outcome switching. IntHout and colleagues (2016) showed that prediction intervals are rarely reported yet routinely change the interpretation of pooled estimates, particularly when heterogeneity is substantial. Turner and colleagues (2012) documented systematic publication bias in antidepressant trials registered with the FDA, illustrating that meta-analytic summaries can overestimate treatment effects when negative studies remain unpublished.

Fragility indices (Walsh et al., 2014; Bakal et al., 2015) have revealed that many statistically significant meta-analyses can be reversed by changing the outcome of a small number of patients in one study. Power analyses by Hedges and Pigott (2001) demonstrated that meta-analyses with fewer than five studies rarely achieve 80% power to detect moderate heterogeneity. GRADE-based certainty assessments (Guyatt et al., 2011) are designed to capture many of these concerns qualitatively, but the agreement between GRADE ratings and objectively detectable flaws has never been systematically evaluated.

### 1.3 What Is Missing: Full-Spectrum, Recomputed Auditing

Prior audit studies have examined one or two flaw domains in isolation — publication bias here, heterogeneity there. None has simultaneously applied a full spectrum of automated detectors to a common corpus of recomputed meta-analyses derived from study-level data. Existing surveys rely on extracted summary statistics, which cannot be recomputed and verified. This leaves open the critical question: when starting from the raw study-level numbers, how prevalent are each of these flaws, how often do they co-occur, and which specialties and time periods are most affected?

### 1.4 The MetaAudit Approach

MetaAudit addresses this gap by applying eleven pre-specified automated detectors to 4,424 Cochrane meta-analyses from 501 systematic reviews, recomputed from scratch using study-level data from the Pairwise70 dataset. No PDFs are processed; all inputs are structured data. This design enables full reproducibility, deterministic reanalysis, and independent verification. The protocol is pre-registered on OSF. All code and outputs are released under open licences consistent with the project's open-access-first mandate.

---

## 2. Methods

### 2.1 Data Source: Pairwise70 Dataset

The Pairwise70 dataset comprises study-level data (event counts, sample sizes, and continuous outcome summaries) extracted from 501 Cochrane systematic reviews. It contains approximately 50,000 RCT-level observations nested within 4,424 pairwise meta-analyses. Data span publication years from approximately 2000 to 2024 and cover a wide range of clinical specialties including cardiology, oncology, psychiatry, gastroenterology, and rheumatology.

All data are drawn from structured Cochrane Review Manager files (RevMan XML), which encode study-level arms, outcome measures, and meta-analysis configurations. No PDF parsing is required. Data are processed entirely from these structured inputs, ensuring reproducibility.

### 2.2 Recomputation Approach

All meta-analyses are recomputed from study-level data rather than extracted summary statistics. For binary outcomes, risk ratios, odds ratios, and risk differences are computed from 2×2 cell counts. For continuous outcomes, standardised mean differences and mean differences are computed from means, standard deviations, and sample sizes. For time-to-event outcomes, log hazard ratios with standard errors are used where available.

Pooling uses REML (Restricted Maximum Likelihood) for tau² estimation in random-effects models. Confidence intervals on pooled estimates use the Hartung-Knapp-Sidik-Jonkman (HKSJ) correction, which provides better coverage than the standard DerSimonian-Laird Wald intervals when the number of studies is small. Both fixed-effects and random-effects estimates are computed for all meta-analyses to enable the model misspecification detector.

### 2.3 The Eleven Flaw Detectors

Each detector applies a pre-specified algorithm and threshold to classify a meta-analysis as PASS, WARN, FAIL, or CRITICAL for that flaw category.

**Detector 1 — Prediction Gap (PI vs. CI)**
A prediction interval (PI) is computed for all meta-analyses with k ≥ 3 studies using the standard formula: pooled estimate ± t_{(k−2), α/2} × sqrt(tau² + SE²). A prediction gap is flagged when the PI crosses the null while the CI does not (WARN), or when the PI is more than twice the width of the CI and the authors report no heterogeneity discussion (FAIL). This follows the recommendation of IntHout et al. (2016) that PIs should be routinely reported.

**Detector 2 — Model Misspecification (FE vs. RE)**
Fixed-effects and random-effects estimates are compared. When I² > 50% and the fixed-effects model is the primary reported model, FAIL is assigned. When I² > 75% under fixed effects, CRITICAL is assigned. This implements the principle that fixed-effects pooling is inappropriate under substantial heterogeneity.

**Detector 3 — Fragility Index (MAFI)**
The Meta-Analysis Fragility Index (MAFI) counts the minimum number of outcome switches (across all studies, one arm only) required to reverse the statistical significance of the pooled estimate. MAFI ≤ 2 = CRITICAL; MAFI ≤ 5 = FAIL; MAFI ≤ 10 = WARN; MAFI > 10 = PASS.

**Detector 4 — Underpowered (k, OIS)**
Statistical power to detect a moderate effect (standardised d = 0.5, alpha = 0.05, power = 0.80) is estimated from k and mean study size. An Optimal Information Size (OIS) check evaluates whether the total N in the meta-analysis meets the threshold for a well-powered single trial. k < 3 with a statistically significant result = WARN; below OIS with a claim of certainty = FAIL.

**Detector 5 — Publication Bias (Egger, Begg, Trim-and-Fill)**
For meta-analyses with k ≥ 5, Egger's test (linear regression of standardised effect on precision) and Begg's rank correlation test are applied. Trim-and-fill is applied to estimate the number of missing studies and the adjusted effect. Egger p < 0.10 = WARN; Egger p < 0.05 combined with trim-and-fill imputing ≥ 2 studies = FAIL; imputing ≥ 5 studies = CRITICAL.

**Detector 6 — Small-Study Effects (Peters, Spearman)**
Peters' test (regression of log odds ratio on inverse of total sample size) and Spearman's rank correlation between effect size and standard error are applied. Peters p < 0.10 = WARN; p < 0.05 = FAIL.

**Detector 7 — Excess Significance (Ioannidis-Trikalinos)**
The observed number of significant studies is compared against the expected number given the pooled effect and study-level power estimates, following Ioannidis and Trikalinos (2007). Significant excess (chi-squared test, p < 0.10) = WARN; p < 0.05 = FAIL.

**Detector 8 — Data Integrity (GRIM)**
The GRIM (Granularity-Related Inconsistency of Means) test checks whether reported group means are consistent with the reported sample sizes for integer-scored outcomes. Any GRIM-inconsistent cell = FAIL. This applies to continuous outcomes from instruments with integer response scales.

**Detector 9 — Study Overlap (Cross-Review)**
Studies appearing in multiple Cochrane reviews within the same broad outcome domain are flagged. Overlap percentage is computed as the fraction of studies in a given meta-analysis that appear in at least one other meta-analysis on a closely related outcome. Overlap > 25% = WARN; > 50% = FAIL. This guards against double-counting of evidence across correlated reviews.

**Detector 10 — Overclaiming (Effect vs. MCID)**
Where a Minimal Clinically Important Difference (MCID) benchmark is available for the outcome (sourced from a curated reference library), the pooled effect is compared against the MCID. A statistically significant effect that falls below the MCID = WARN. A pooled effect whose 95% CI lies entirely below the MCID = FAIL, flagging a precision-significance fallacy.

**Detector 11 — Certainty-Outcome Mismatch (GRADE vs. Automated)**
Where GRADE certainty ratings are available in the source review (High/Moderate/Low/Very Low), these are compared against the automated severity score derived from detectors 1–10. A GRADE rating of High combined with a FAIL or CRITICAL automated score = CRITICAL mismatch. Moderate combined with CRITICAL = FAIL mismatch. This tests the calibration of expert GRADE judgments against computational signals.

### 2.4 Severity Classification

Each meta-analysis receives an overall severity score based on its worst detector outcome:

| Score    | Criteria                                                  |
|----------|-----------------------------------------------------------|
| PASS     | No flaw detectors triggered at WARN or above              |
| WARN     | One or more detectors at WARN level only                  |
| FAIL     | At least one detector at FAIL level                       |
| CRITICAL | At least one detector at CRITICAL level                   |

A composite vulnerability index (0–100) will be derived from a weighted sum of detector outcomes, with weights pre-specified based on clinical impact (fragility and model misspecification weighted most heavily).

### 2.5 Correlator Analysis

Following prevalence estimation, a correlator analysis will examine:

1. **Co-occurrence matrix:** Pairwise Phi coefficients between all 11 binary (triggered/not) flaw indicators. Visualised as a heatmap and minimum-spanning-tree network.
2. **Specialty stratification:** Flaw prevalence broken down by Cochrane Review Group (cardiology, oncology, psychiatry, etc.). Pairwise chi-squared tests with Bonferroni correction.
3. **Temporal trends:** Logistic regression of flaw prevalence on publication year (2000–2024), adjusting for specialty. Assessed for linear trend.
4. **Effect size and k modifiers:** Logistic regression of each flaw indicator on log(k), log(N), and effect size magnitude.

---

## 3. Analysis Plan

### 3.1 Primary Outcomes

The primary outcome for each of the eleven detectors is its prevalence (proportion of 4,424 meta-analyses triggering that detector at any level ≥ WARN), reported with exact binomial 95% confidence intervals.

### 3.2 Secondary Outcomes

1. FAIL+CRITICAL prevalence for each detector (a stricter threshold).
2. Pairwise co-occurrence rates (Phi coefficients) for all 55 detector pairs.
3. Specialty-stratified prevalence for the five most prevalent flaws.
4. Temporal trend: linear trend in annual flaw prevalence over 2000–2024.
5. Overall severity distribution: proportions of PASS/WARN/FAIL/CRITICAL across all 4,424 meta-analyses.
6. Calibration of GRADE vs. automated severity (detector 11).

### 3.3 Sensitivity Analyses

1. Restricting to meta-analyses with k ≥ 5 (more stable statistical tests).
2. Using DerSimonian-Laird tau² instead of REML.
3. Applying a fixed-effects-only version of detector 2 (no model comparison).
4. Excluding single-outcome meta-analyses (k = 1 or k = 2) from power-dependent detectors.
5. Restricting to binary outcomes only (for comparability with published fragility index studies).

### 3.4 Pre-Specification and Reproducibility

All thresholds, detector algorithms, and analysis steps are pre-specified in this protocol prior to data analysis. The protocol will be registered on OSF. The analysis pipeline is implemented in Python (version ≥ 3.11) with pinned package versions. All random seeds are fixed. Outputs are produced as TruthCert versioned capsules, each containing: inputs, code, outputs, content hashes, and an audit log. The complete pipeline will be released on GitHub under an MIT licence. No API keys or network access are required for the analysis; all computations run offline on the Pairwise70 dataset.

---

## 4. Ethics and Registration

This study involves reanalysis of published, de-identified aggregate data from Cochrane systematic reviews. No individual patient data are used. No ethics committee approval is required. OSF pre-registration is planned at [URL to be inserted prior to analysis]. The study is observational and involves no interventions.

---

## 5. Limitations

The scope of this audit is restricted to Cochrane reviews represented in the Pairwise70 dataset, which may not be representative of all published meta-analyses (including non-Cochrane and non-English-language reviews). MCID thresholds are not available for all outcomes; detector 10 will therefore apply to a subset only. GRIM testing (detector 8) applies only to continuous outcomes from integer-scored instruments. Certainty-outcome mismatch detection (detector 11) requires GRADE ratings in the source review; coverage will be partial. The automated severity score should be interpreted as a computational audit signal, not a replacement for expert methodological assessment.

---

## 6. Expected Impact

If systematic flaw co-occurrence is observed — for example, that underpowered meta-analyses are also more likely to be fragile and to show evidence of small-study effects — this would provide quantitative justification for multi-criterion quality filters in evidence grading systems such as GRADE. The openly released severity dashboard would allow guideline developers to query any Cochrane meta-analysis in the corpus and retrieve its automated flaw profile before incorporating its findings into a recommendation. This represents a scalable, reproducible approach to evidence quality surveillance that complements existing qualitative tools such as AMSTAR-2.

---

## 7. AI Disclosure Statement

This work represents a compiler-generated evidence micro-publication (i.e., a structured, pipeline-based synthesis output). AI is used as a constrained synthesis engine operating on structured inputs and predefined rules, rather than as an autonomous author. Deterministic components of the pipeline, together with versioned, reproducible evidence capsules (TruthCert), are designed to support transparent and auditable outputs. All results and text were reviewed and verified by the author, who takes full responsibility for the content. The workflow operationalises key transparency and reporting principles consistent with CONSORT-AI/SPIRIT-AI, including explicit input specification, predefined schemas, logged human–AI interaction, and reproducible outputs.

---

## 8. References

1. Ioannidis JPA, Trikalinos TA. An exploratory test for an excess of significant findings. *Clinical Trials*. 2007;4(3):245–253.

2. IntHout J, Ioannidis JPA, Rovers MM, Goeman JJ. Plea for routinely presenting prediction intervals in meta-analysis. *BMJ Open*. 2016;6(7):e010247.

3. Walsh M, Srinathan SK, McAuley DF, et al. The statistical significance of randomized controlled trial results is frequently fragile: a case for a Fragility Index. *Journal of Clinical Epidemiology*. 2014;67(6):622–628.

4. Hedges LV, Pigott TD. The power of statistical tests in meta-analysis. *Psychological Methods*. 2001;6(3):203–217.

5. Shea BJ, Reeves BC, Wells G, et al. AMSTAR 2: a critical appraisal tool for systematic reviews that include randomised or non-randomised studies of healthcare interventions. *BMJ*. 2017;358:j4008.

6. Guyatt G, Oxman AD, Akl EA, et al. GRADE guidelines: 1. Introduction — GRADE evidence profiles and summary of findings tables. *Journal of Clinical Epidemiology*. 2011;64(4):383–394.

7. Turner EH, Matthews AM, Linardatos E, Tell RA, Rosenthal R. Selective publication of antidepressant trials and its influence on apparent efficacy. *New England Journal of Medicine*. 2008;358(3):252–260.

8. Hartung J, Knapp G. A refined method for the meta-analysis of controlled clinical trials with binary outcome. *Statistics in Medicine*. 2001;20(24):3875–3889.

9. Higgins JPT, Thompson SG. Quantifying heterogeneity in a meta-analysis. *Statistics in Medicine*. 2002;21(11):1539–1558.

10. Brown AW, Kaiser KA, Allison DB. Issues with data and analyses: errors, underlying themes, and potential solutions. *Proceedings of the National Academy of Sciences*. 2018;115(11):2563–2570.
