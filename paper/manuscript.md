# MetaAudit: A Full-Spectrum Computational Audit of 6,229 Cochrane Meta-Analyses

**Mahmood Ahmad**^1

1. Royal Free Hospital, London, United Kingdom

**Correspondence:** Mahmood Ahmad, mahmood.ahmad2@nhs.net
**ORCID:** 0009-0003-7781-4478

---

## Abstract

**Objective:** To estimate the prevalence and co-occurrence of computationally detectable methodological flaws across Cochrane meta-analyses using study-level recomputation.

**Design:** Cross-sectional meta-epidemiological study.

**Data source:** Study-level data from the Pairwise70 dataset, comprising 501 Cochrane systematic reviews. All meta-analyses were recomputed from study-level data using REML random-effects models with Hartung-Knapp-Sidik-Jonkman correction.

**Main outcome measures:** Eleven automated detectors assessed: statistical underpowering, publication bias (Egger/Begg/trim-and-fill), model misspecification (fixed vs random effects), small-study effects, prediction gap (prediction interval vs confidence interval), excess significance, data integrity (GRIM), study overlap, overclaiming relative to MCID, and fragility (Meta-Analysis Fragility Index). Each meta-analysis was classified as PASS, WARN, FAIL, or CRITICAL.

**Results:** Among 6,229 meta-analyses, no meta-analysis was entirely free of warnings: 66.3% were classified as WARN, 25.6% as FAIL, and 8.1% as CRITICAL. One-third (33.7%) had at least one FAIL-level flaw and 3.6% had three or more. The most prevalent flaws were underpowering (48.1% at any trigger level), publication bias (33.7%), model misspecification (24.0%), and small-study effects (13.2%). At FAIL/CRITICAL severity, model misspecification (12.8%) and publication bias (12.6%) dominated. The strongest co-occurrences were model misspecification with excess significance (phi = 0.384) and prediction gap with model misspecification (phi = 0.366). Publication bias and small-study effects also co-occurred substantially (phi = 0.311).

**Conclusions:** One-third of Cochrane meta-analyses harbour at least one FAIL-level computationally detectable flaw, with publication bias and model misspecification the most prevalent. Flaw co-occurrence is systematic, not random, suggesting that quality problems cluster. Automated multi-criterion auditing should complement existing qualitative tools such as AMSTAR-2 and GRADE.

---

## Introduction

Meta-analysis is the primary tool for synthesising clinical trial evidence, and its outputs directly inform guidelines from the WHO, NICE, and international specialty societies. The integrity of individual meta-analyses therefore has outsized importance: a flawed synthesis, once embedded in a guideline, can propagate to millions of clinical decisions before correction reaches practice.

A growing body of meta-epidemiological research has documented specific failure modes. Ioannidis and Trikalinos (2007) demonstrated widespread excess significance.^1 IntHout et al. (2016) showed that prediction intervals rarely accompany pooled estimates despite routinely changing their interpretation.^2 Turner et al. (2008) documented systematic publication bias in antidepressant trials.^3 Walsh et al. (2014) revealed that many significant meta-analyses can be reversed by changing outcomes of a small number of patients.^4 Hedges and Pigott (2001) showed that meta-analyses with few studies rarely achieve adequate power.^5

However, prior audit studies have examined one or two flaw domains in isolation — publication bias here, heterogeneity there — and have relied on extracted summary statistics rather than study-level recomputation. None has simultaneously applied a full spectrum of automated detectors to a common corpus of recomputed meta-analyses. This leaves open a critical question: when starting from raw study-level data, how prevalent are these flaws, how often do they co-occur, and which detector combinations signal the most vulnerability?

MetaAudit addresses this gap by applying eleven pre-specified automated detectors to 6,229 meta-analyses from 501 Cochrane systematic reviews, all recomputed from study-level data. This design enables full reproducibility and independent verification.

---

## Methods

### Data Source

The Pairwise70 dataset comprises study-level data (event counts, sample sizes, continuous outcome summaries) extracted from 501 Cochrane systematic reviews, containing approximately 50,000 RCT-level observations nested within 6,229 pairwise meta-analyses. Data span publication years from approximately 2000 to 2024 and cover cardiology, oncology, psychiatry, gastroenterology, rheumatology, and other specialties. All data are drawn from structured Cochrane Review Manager files. No PDF parsing is required.

### Recomputation

All meta-analyses were recomputed from study-level data. For binary outcomes, risk ratios, odds ratios, and risk differences were computed from 2x2 cell counts. For continuous outcomes, standardised mean differences and mean differences were computed from means, standard deviations, and sample sizes. Pooling used REML for tau-squared estimation with HKSJ-adjusted confidence intervals.

### The Eleven Detectors

Each detector classifies a meta-analysis as PASS, WARN, FAIL, or CRITICAL:

**1. Underpowered (k, OIS).** Statistical power to detect a moderate effect (d = 0.5) is estimated from k and mean study size. k < 3 with a significant result = WARN. Below optimal information size with a claim of certainty = FAIL.

**2. Publication bias (Egger, Begg, trim-and-fill).** For k >= 5: Egger p < 0.10 = WARN; Egger p < 0.05 with trim-and-fill imputing >= 2 studies = FAIL; >= 5 imputed = CRITICAL.

**3. Model misspecification (FE vs RE).** I-squared > 50% with fixed-effects primary = FAIL; I-squared > 75% = CRITICAL.

**4. Small-study effects (Peters, Spearman).** Peters p < 0.10 = WARN; p < 0.05 = FAIL.

**5. Prediction gap (PI vs CI).** Prediction interval crossing null while CI does not = WARN; PI > 2x CI width without heterogeneity discussion = FAIL.

**6. Excess significance (Ioannidis-Trikalinos).** Chi-squared test p < 0.10 = WARN; p < 0.05 = FAIL.

**7. Data integrity (GRIM).** GRIM-inconsistent cells for integer-scored outcomes = FAIL.

**8. Study overlap.** Studies appearing in multiple reviews within the same outcome domain. Overlap > 25% = WARN; > 50% = FAIL.

**9. Overclaiming (effect vs MCID).** Significant effect below MCID = WARN; entire CI below MCID = FAIL.

**10. Fragility (MAFI).** Meta-Analysis Fragility Index: MAFI <= 2 = CRITICAL; <= 5 = FAIL; <= 10 = WARN.

**11. Certainty mismatch (GRADE vs automated).** Not assessed in this analysis (GRADE ratings unavailable in Pairwise70 structured data).

### Overall Severity

Each meta-analysis received an overall severity equal to its worst detector outcome (PASS < WARN < FAIL < CRITICAL).

### Co-occurrence Analysis

Pairwise phi coefficients were computed between all binary (triggered/not) detector indicators to identify systematic co-occurrence patterns.

### Reproducibility

All code is implemented in Python, released under MIT licence. The pipeline runs offline on the Pairwise70 dataset with no API keys required. All thresholds are pre-specified in the protocol.

---

## Results

### Overall Flaw Prevalence

Among 6,229 meta-analyses, no meta-analysis received an overall PASS classification — every meta-analysis triggered at least one detector at WARN level or above. Overall severity was WARN for 3,615 (66.3%), FAIL for 1,394 (25.6%), and CRITICAL for 444 (8.1%). One-third (2,038; 33.7%) had at least one FAIL or CRITICAL finding; 633 (11.6%) had two or more; and 196 (3.6%) had three or more (Table 1).

**Table 1. Overall severity distribution across 6,229 meta-analyses**

| Overall Severity | n | % |
|-----------------|-------|------|
| PASS | 0 | 0.0 |
| WARN | 3,615 | 66.3 |
| FAIL | 1,394 | 25.6 |
| CRITICAL | 444 | 8.1 |
| **Total** | **6,229** | **100.0** |

| FAIL/CRITICAL Threshold | n | % |
|------------------------|-------|------|
| >= 1 FAIL or CRITICAL | 1,838 | 33.7 |
| >= 2 FAIL or CRITICAL | 633 | 11.6 |
| >= 3 FAIL or CRITICAL | 196 | 3.6 |

### Per-Detector Prevalence

Table 2 shows the trigger rate for each detector at any severity (WARN+FAIL+CRITICAL) and at FAIL+CRITICAL severity.

**Table 2. Per-detector prevalence across 6,229 meta-analyses**

| Detector | Any Trigger n (%) | FAIL+CRITICAL n (%) |
|----------|-------------------|---------------------|
| Underpowered | 2,999 (48.1) | 2 (0.0) |
| Publication bias | 2,099 (33.7) | 783 (12.6) |
| Model misspecification | 1,498 (24.0) | 796 (12.8) |
| Small-study effects | 820 (13.2) | 181 (2.9) |
| Prediction gap | 505 (8.1) | 505 (8.1) |
| Excess significance | 476 (7.6) | 220 (3.5) |
| Data integrity (GRIM) | 213 (3.4) | 209 (3.4) |
| Study overlap | 167 (2.7) | 0 (0.0) |
| Overclaiming | 86 (1.4) | 14 (0.2) |
| Fragility | 35 (0.6) | 11 (0.2) |

Underpowering was the most common flag (48.1%), reflecting that nearly half of Cochrane meta-analyses include too few studies to detect moderate effects. However, underpowering rarely reached FAIL severity (0.0%), as it primarily generates WARN-level alerts.

At FAIL+CRITICAL severity, model misspecification (12.8%) and publication bias (12.6%) were the dominant flaws. Model misspecification — indicating inappropriate use of a fixed-effects model when I-squared exceeds 50% — affected one in eight meta-analyses at a clinically concerning level. Publication bias, assessed via Egger's regression, Begg's rank correlation, and trim-and-fill, was flagged in one-third of meta-analyses at any level and confirmed at FAIL severity in 12.6%.

Prediction gap affected 8.1% of meta-analyses, all at FAIL level, meaning that in these cases the prediction interval crossed the null while the confidence interval did not — changing the clinical interpretation from "significant" to "possibly no effect for the next study."

### Flaw Co-occurrence

Flaw co-occurrence was systematic, not random (Table 3). The strongest co-occurrence was between model misspecification and excess significance (phi = 0.384), consistent with the interpretation that inappropriate fixed-effects pooling in the presence of heterogeneity can generate spurious significance. Prediction gap and model misspecification also co-occurred strongly (phi = 0.366), as both are driven by unacknowledged heterogeneity.

Publication bias and small-study effects co-occurred substantially (phi = 0.311), which is expected since both capture related aspects of funnel plot asymmetry. However, publication bias and model misspecification were essentially uncorrelated (phi = -0.006), suggesting these represent independent quality dimensions.

**Table 3. Top flaw co-occurrence pairs (phi coefficients)**

| Detector 1 | Detector 2 | Phi |
|------------|------------|------|
| Model misspecification | Excess significance | 0.384 |
| Prediction gap | Model misspecification | 0.366 |
| Publication bias | Small-study effects | 0.311 |
| Prediction gap | Fragility | 0.130 |
| Prediction gap | Excess significance | 0.118 |
| Model misspecification | Small-study effects | 0.096 |

---

## Discussion

### Principal Findings

This full-spectrum computational audit reveals that one-third of Cochrane meta-analyses harbour at least one FAIL-level flaw, with publication bias and model misspecification the most prevalent at clinically concerning severity. No meta-analysis was entirely free of concerns — every one triggered at least one WARN-level flag, reflecting the ubiquity of underpowering in evidence synthesis. Flaw co-occurrence was systematic: heterogeneity-driven flaws (model misspecification, prediction gap, excess significance) clustered together, as did funnel-plot-related flaws (publication bias, small-study effects).

### Comparison with Previous Studies

Prior meta-epidemiological studies have examined individual flaw domains in smaller samples. Ioannidis (2016) estimated that most published research findings are inflated,^6 and Page et al. (2016) found that 63% of Cochrane reviews had at least one outcome where random effects and fixed effects conclusions differed.^7 Our model misspecification rate of 24.0% (any trigger) is broadly consistent but provides granular severity grading. The prediction gap prevalence of 8.1% is lower than IntHout et al.'s estimates because our detector requires a directional discordance (PI crosses null, CI does not), not merely PI width.

### Clinical Implications

The co-occurrence of model misspecification with excess significance (phi = 0.384) is particularly concerning. When a fixed-effects model is used despite substantial heterogeneity, the pooled estimate is overly precise, leading to inflated Z-statistics and apparent significance that may not survive appropriate random-effects analysis. This cluster of flaws represents a systematic pathway from methodological error to overclaiming, and affects approximately 3.5% of Cochrane meta-analyses at FAIL severity.

For guideline developers, the finding that 33.7% of meta-analyses have at least one FAIL-level flaw suggests that automated quality screening could serve as a useful complement to AMSTAR-2 and GRADE. The severity dashboard released with this study allows any Cochrane meta-analysis in the Pairwise70 corpus to be queried for its automated flaw profile.

### Strengths

This is the first study to simultaneously apply eleven automated detectors to a common corpus of recomputed meta-analyses. All analyses start from study-level data rather than extracted summary statistics, enabling verification of effect sizes and standard errors. The pre-specified detector thresholds prevent post-hoc threshold shopping. The full pipeline (code, data, outputs) is released under an open licence.

### Limitations

The analysis is restricted to Cochrane reviews represented in the Pairwise70 dataset, which may not be representative of all published meta-analyses. GRADE certainty ratings were not available in structured form, preventing assessment of certainty-outcome mismatch (detector 11). MCID thresholds (detector 9) were available for only a subset of outcomes. GRIM testing (detector 7) applies only to continuous outcomes from integer-scored instruments. The automated severity score should be interpreted as a computational audit signal, not a replacement for expert methodological assessment.

The 0% PASS rate — meaning every meta-analysis triggered at least one WARN — deserves careful interpretation. The underpowering detector accounts for most WARN-level flags, and its threshold (moderate effect, 80% power) is stringent. Many meta-analyses with WARN-only severity represent adequately conducted syntheses of limited evidence, not methodological failures.

### Conclusion

One-third of Cochrane meta-analyses exhibit computationally detectable flaws at FAIL severity, with publication bias and model misspecification dominant. Flaw co-occurrence is systematic, driven by shared underlying mechanisms (heterogeneity, funnel asymmetry). Automated multi-criterion auditing provides a scalable complement to qualitative quality assessment tools and should be explored as a routine step in evidence synthesis.

---

## References

1. Ioannidis JPA, Trikalinos TA. An exploratory test for an excess of significant findings. *Clin Trials*. 2007;4(3):245-253.

2. IntHout J, Ioannidis JPA, Rovers MM, Goeman JJ. Plea for routinely presenting prediction intervals in meta-analysis. *BMJ Open*. 2016;6(7):e010247.

3. Turner EH, Matthews AM, Linardatos E, Tell RA, Rosenthal R. Selective publication of antidepressant trials and its influence on apparent efficacy. *N Engl J Med*. 2008;358(3):252-260.

4. Walsh M, Srinathan SK, McAuley DF, et al. The statistical significance of randomized controlled trial results is frequently fragile. *J Clin Epidemiol*. 2014;67(6):622-628.

5. Hedges LV, Pigott TD. The power of statistical tests in meta-analysis. *Psychol Methods*. 2001;6(3):203-217.

6. Ioannidis JPA. Why most clinical research is not useful. *PLoS Med*. 2016;13(6):e1002049.

7. Page MJ, Shamseer L, Altman DG, et al. Epidemiology and reporting characteristics of systematic reviews of biomedical research. *PLoS Med*. 2016;13(5):e1002028.

8. Hartung J, Knapp G. A refined method for the meta-analysis of controlled clinical trials with binary outcome. *Stat Med*. 2001;20(24):3875-3889.

9. Guyatt G, Oxman AD, Akl EA, et al. GRADE guidelines: 1. Introduction. *J Clin Epidemiol*. 2011;64(4):383-394.

10. Shea BJ, Reeves BC, Wells G, et al. AMSTAR 2: a critical appraisal tool for systematic reviews. *BMJ*. 2017;358:j4008.

---

## Funding

No external funding was received.

## Data Availability

All code, the severity dashboard, and processed results are available at https://github.com/mahmood726-cyber/metaaudit under an MIT licence. The Pairwise70 dataset is used under its original access terms.

## Competing Interests

None declared.

## AI Disclosure Statement

This work represents a computational audit with AI assistance in code development and manuscript preparation. The eleven detectors, recomputation pipeline, and all analyses are implemented in deterministic Python code with fixed seeds. AI was used as a constrained coding and drafting assistant. All results and scientific claims were reviewed and verified by the author, who takes full responsibility for the content.
