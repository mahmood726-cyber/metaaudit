# MetaAudit — Design Specification

**A Computational Audit of Evidence Synthesis**

*"The first full-spectrum, automated diagnostic of meta-analytic evidence"*

**Date:** 2026-03-27
**Author:** Mahmood Ahmad (Royal Free Hospital, London)
**Project directory:** `C:\MetaAudit\`
**Status:** Design approved, pending implementation

---

## 1. Problem Statement

Meta-analyses are treated as the highest level of evidence in medicine, yet no study has ever run a comprehensive, multi-dimensional quality audit across a large corpus of meta-analyses using study-level data. Prior meta-epidemiological studies have checked 1–2 flaws on 100–300 reviews manually. Systematic, computational, full-spectrum auditing does not exist.

**Core claim this project will test:** The majority of Cochrane meta-analyses — the gold standard of evidence synthesis — have at least one detectable serious flaw when subjected to automated diagnostic checks.

## 2. What Makes This Novel

1. **Scale:** 4,424 meta-analyses from 501 Cochrane reviews (~50,000 RCTs)
2. **Breadth:** 11 independent flaw detectors across 4 categories (statistical, bias, integrity, interpretation)
3. **Study-level recomputation:** All statistics recomputed from raw data, not trusted from summaries
4. **Flaw co-occurrence:** First study to map how flaws cluster and correlate
5. **Fully computational:** Every finding reproducible from code + data

### Prior work this builds on

| Study | N | Flaws checked | Key finding |
|-------|---|---------------|-------------|
| IntHout, Ioannidis et al. (2016) | 3,263 Cochrane MAs | Prediction intervals | 72.4% of significant MAs have PIs crossing null |
| Ioannidis (2005) | Theoretical model | False positive rates | Most findings likely false |
| Fanelli et al. (2017) | 1,910 MAs | Small-study effects | 19% show small-study effects |
| AMSTAR-2 audits (2024-25) | ~150-300 | Methodological quality | 90% rated "critically low" |
| Ahmad — PredictionGap | 403 Cochrane | PI/CI ratio | 69.8% significant MAs have PIs crossing null |
| Ahmad — MAFI | 4,424 Cochrane | Fragility index | Published in Research Synthesis Methods |
| Ahmad — Bias Forensics | 307 reviews | 8 pub bias methods | 16.1% high risk |
| Ahmad — OverlapDetector | 501 reviews | Study overlap | CCA = 0.0001 |

## 3. Data Source

### Pairwise70 Dataset
- **Location:** `C:\Users\user\OneDrive - NHS\Documents\Pairwise70\`
- **Format:** 501 `.rda` files (R binary), each containing study-level data for one Cochrane review
- **Coverage:** 501 unique Cochrane reviews, 4,424 meta-analyses, ~50,000 individual RCTs
- **Fields (binary outcomes):** Study, Study.year, Comparison, Outcome, Subgroup, Experimental.cases, Experimental.N, Control.cases, Control.N
- **Fields (continuous outcomes):** Study, Study.year, Comparison, Outcome, Subgroup, Experimental.mean, Experimental.SD, Experimental.N, Control.mean, Control.SD, Control.N
- **Metadata:** review_doi, review_title, comparison_id, outcome_id
- **No PDFs required.** All data is structured and machine-readable.

### Pre-computed cross-validation data
- `MAFI_all_variants.csv` — 4,424 MAs with fragility scores (for Module 3 validation)
- `analysis_results.csv` — 32,062 rows of pooled results (for recomputation validation)

## 4. Architecture: Hybrid (Python Engine + HTML Dashboard)

### Rationale
- Python for statistical rigour, testability, and native .rda reading
- HTML for interactive exploration and journal supplementary material
- JSON intermediate connects both — single source of truth

### Data flow
```
501 .rda files (study-level)
     │
     ▼
Python loader (pyreadr)
     │
     ▼
Standardised DataFrame per review
     │
     ▼
Recompute layer (pooled effects, I², tau², PI)
     │
     ▼
11 Flaw Detectors (run independently per MA)
     │
     ▼
Results JSON (one record per MA × flaw)
     │
     ├──▶ Correlator (co-occurrence, specialty, temporal)
     ├──▶ Paper tables (CSV/LaTeX)
     └──▶ HTML Dashboard (interactive)
```

### Directory structure
```
C:\MetaAudit\
├── metaaudit/                    # Python package
│   ├── __init__.py
│   ├── loader.py                 # Read .rda → standardised DataFrames
│   ├── recompute.py              # Pool effects, I², tau², PI from raw data
│   ├── detectors/                # One module per flaw
│   │   ├── __init__.py
│   │   ├── prediction_gap.py     # Module 1
│   │   ├── model_misspec.py      # Module 2
│   │   ├── fragility.py          # Module 3
│   │   ├── underpowered.py       # Module 4
│   │   ├── pub_bias.py           # Module 5
│   │   ├── small_study.py        # Module 6
│   │   ├── excess_sig.py         # Module 7
│   │   ├── integrity.py          # Module 8
│   │   ├── overlap.py            # Module 9
│   │   ├── overclaiming.py       # Module 10
│   │   └── certainty_mismatch.py # Module 11
│   ├── severity.py               # PASS/WARN/FAIL/CRITICAL logic
│   ├── correlator.py             # Flaw co-occurrence analysis
│   └── export.py                 # JSON + CSV + LaTeX output
├── tests/                        # One test file per detector + integration
│   ├── test_loader.py
│   ├── test_recompute.py
│   ├── test_prediction_gap.py
│   ├── ... (one per detector)
│   └── test_integration.py       # Full pipeline on 5 known reviews
├── dashboard/
│   └── index.html                # Single-file interactive dashboard
├── results/                      # Output JSON/CSV (gitignored)
├── run_audit.py                  # CLI entry point
└── requirements.txt              # pyreadr, numpy, scipy, pandas
```

## 5. Severity Classification

Uniform across all 11 modules:

| Level | Meaning | Colour |
|-------|---------|--------|
| **PASS** | No flaw detected | Green |
| **WARN** | Minor concern, doesn't invalidate conclusions | Amber |
| **FAIL** | Serious flaw that could change the conclusion | Red |
| **CRITICAL** | Multiple converging signals — conclusion unreliable | Dark red |

## 6. The 11 Flaw Detection Modules

### Category A: Statistical Flaws

**Module 1 — Prediction Gap**
- Recompute 95% PI using HKSJ from study-level data
- FAIL: CI excludes null but PI includes it
- CRITICAL: PI includes effects in the opposite direction
- Benchmark: IntHout et al. 72.4%, PredictionGap 69.8%

**Module 2 — Model Misspecification**
- Recompute I² and tau² from study-level data
- FAIL: I²>50% but fixed-effect model used
- WARN: I²>75% with no subgroup exploration
- Also flags: OR used for common outcomes (>20% prevalence) where RR is more appropriate; MD used when scales differ (SMD needed)

**Module 3 — Fragility (MAFI)**
- Compute fragility index from study-level data
- Cross-validate against MAFI_all_variants.csv
- FAIL: MAFI ≤ 2
- WARN: MAFI ≤ 5

**Module 4 — Underpowered MA**
- WARN: k<5 studies
- FAIL: k<3 with "significant" conclusion
- Also: total N < optimal information size (OIS)

### Category B: Bias Detection

**Module 5 — Publication Bias**
- Egger's test, Begg's test, trim-and-fill
- Requires k≥10 (below: "insufficient data", not PASS)
- FAIL: ≥2 tests converge on asymmetry
- Report adjusted effect from trim-and-fill

**Module 6 — Small-Study Effects**
- Funnel asymmetry + Peters' test (binary) / Egger (continuous)
- FAIL: significant asymmetry AND small studies show larger effects
- Distinct from Module 5 — small-study effects aren't always publication bias

**Module 7 — Excess Significance**
- Ioannidis & Trikalinos test: observed vs expected significant studies
- FAIL: O/E ratio > 1.5 with p<0.10
- Signals selective reporting or p-hacking at study level

### Category C: Integrity & Overlap

**Module 8 — Data Integrity (Forensic)**
- Impossible event counts (events > N)
- Duplicate effect sizes across studies
- Terminal digit patterns
- GRIM/SPRITE consistency checks
- FAIL: impossible values; WARN: suspicious patterns

**Module 9 — Study Overlap**
- Cross-reference study identifiers across all 501 reviews
- WARN: >30% study overlap with another review
- FAIL: overlapping reviews reach contradictory conclusions
- Uses OverlapDetector logic

### Category D: Interpretation

**Module 10 — Overclaiming**
- Compare effect size against clinical relevance thresholds
- FAIL: conclusion claims "effective" but effect below MCID
- Uses published MCIDs where available; flags for manual review otherwise

**Module 11 — Certainty-Outcome Mismatch**
- Compare GRADE certainty (where available) against MetaAudit severity
- CRITICAL: GRADE = "High" but ≥3 modules FAIL
- FAIL: GRADE = "Moderate" but ≥4 modules FAIL
- The "killer" finding — Cochrane's own certainty doesn't survive automated scrutiny

## 7. Correlator Analysis

After all 11 detectors run, the correlator builds:

1. **Flaw prevalence table:** % of MAs failing each module
2. **Co-occurrence matrix:** Phi coefficients between all flaw pairs (11×11)
3. **Specialty clustering:** Flaw profiles by medical specialty (using Cochrane review group as proxy)
4. **Temporal trends:** Are newer reviews better or worse? (using Study.year and review publication date)
5. **Severity score per review:** Weighted sum across modules for ranking
6. **GRADE discordance rate:** % of high/moderate certainty conclusions that fail automated checks

## 8. HTML Dashboard

Single-file HTML app loading pre-computed `audit_results.json`. No browser-side computation.

### View 1: Global Summary ("The Verdict")
- Hero numbers: "X% of 4,424 MAs have ≥1 FAIL", "Y% have ≥3 FAILs"
- Bar chart: prevalence per flaw module
- Severity distribution: PASS/WARN/FAIL/CRITICAL

### View 2: Flaw Co-occurrence Heatmap
- 11×11 phi correlation matrix
- Click cell → list of reviews with both flaws

### View 3: Review Explorer
- Sortable/filterable table of 501 reviews
- Columns: review ID, title, specialty, k, severity, mini heatmap strip (11 modules)
- Click row → detail panel with per-MA results
- Filters: specialty, severity, specific flaw, k range, year

### View 4: Specialty Comparison
- Grouped bar chart: flaw prevalence by specialty
- Radar/spider chart per specialty

### Constraints
- Single HTML file, no build step, no server
- Canvas-based charts (no D3 dependency)
- Dark mode, WCAG AA contrast
- Print-friendly mode for journal submission

## 9. Testing & Validation

### Layer 1: Unit tests per detector (55+ tests)
Each detector gets 5+ tests:
- Known PASS case
- Known FAIL case
- Edge: k=2, k=1, zero events, zero variance

### Layer 2: Cross-validation against existing tools (20+ tests)
- Module 1 vs PredictionGap (403 reviews, expect ~69.8%)
- Module 3 vs MAFI_all_variants.csv (4,424 MAs)
- Modules 5-7 vs Bias Forensics (307 reviews)
- Module 9 vs OverlapDetector (501 reviews, CCA = 0.0001)
- Recompute layer vs R metafor on 10 benchmark datasets

### Layer 3: Integration test
Full pipeline on 5 hand-picked reviews:
- One "clean" review (expect mostly PASS)
- One with known high heterogeneity
- One with known publication bias
- One with very small k
- One with known fragility

### Paper validation
- Sensitivity analysis: findings under ±10% threshold shifts
- Detector agreement rates
- Pre-register analysis protocol on OSF

## 10. Publication Strategy

### Publication 1: Protocol Paper
- **Target:** BMJ Open / Systematic Reviews
- **Content:** Rationale, dataset, 11 modules with thresholds, analysis plan
- **Filed with:** OSF pre-registration
- **Timing:** Written during/after Phase 1 (modules defined), published BEFORE running full audit
- **Also:** E156-format 156-word micro-protocol via Synthesis course/platform

### Publication 2: Main Paper
- **Target:** BMJ (primary) / PLOS Medicine (secondary) / J Clin Epidemiol (tertiary)
- **Title candidates:**
  1. "Full-Spectrum Audit of 4,424 Cochrane Meta-Analyses Reveals Systematic Flaws in Evidence Synthesis"
  2. "How Reliable Is the Reliable Evidence? A Computational Diagnostic of Cochrane Systematic Reviews"
  3. "The Evidence Crisis: 11 Automated Checks Expose Pervasive Weaknesses in Meta-Analytic Evidence"
- **Structure:** Introduction → Methods → Results (5 sections: prevalence, co-occurrence, specialty, GRADE mismatch, case studies) → Discussion
- **Key figures:** Prevalence bars, co-occurrence heatmap, specialty radars, GRADE Sankey diagram
- **Supplementary:** Interactive HTML dashboard + full results CSV + code

### Publication 3: Tool Paper
- **Target:** JOSS or F1000Research Software Tool
- **Content:** MetaAudit as reusable open-source tool
- **Timing:** After main paper accepted

### AI Disclosure Statement (required in all protocols and E156 micro-papers)

> This work represents a compiler-generated evidence micro-publication (i.e., a structured, pipeline-based synthesis output). AI is used as a constrained synthesis engine operating on structured inputs and predefined rules, rather than as an autonomous author. Deterministic components of the pipeline, together with versioned, reproducible evidence capsules (TruthCert), are designed to support transparent and auditable outputs. All results and text were reviewed and verified by the author, who takes full responsibility for the content. The workflow operationalises key transparency and reporting principles consistent with CONSORT-AI/SPIRIT-AI, including explicit input specification, predefined schemas, logged human–AI interaction, and reproducible outputs.

### Framing
- NOT claiming Cochrane is bad — claiming even the best evidence has measurable, systematic weaknesses
- NOT claiming MAs should be abandoned — claiming they need automated quality checks as standard practice
- MetaAudit itself becomes the proposed solution

## 11. Implementation Phases

| Phase | What | Depends on |
|-------|------|-----------|
| **Phase 1** | Python engine: loader + recompute + 11 detectors + tests | — |
| **Phase 2** | Run full audit on 501 reviews, export results JSON | Phase 1 tests pass |
| **Phase 3** | Correlator analysis (co-occurrence, specialty, temporal) | Phase 2 |
| **Phase 4** | HTML dashboard | Phase 2 results |
| **Phase 5** | Protocol paper + OSF registration + E156 micro-protocol | Phase 1 (modules defined) |
| **Phase 6** | Main manuscript | Phases 2-4 complete |

Phases 4 and 5 can run in parallel.

## 12. Dependencies

**Python (minimal):**
- `pyreadr` — read .rda files
- `numpy` — numerical computation
- `scipy` — statistical tests
- `pandas` — data handling

**No ML, no heavy frameworks, no network access, no API keys.**

**R (validation only):**
- `metafor` — cross-validate recomputed effects
- Available at `C:\Program Files\R\R-4.5.2\bin\Rscript.exe`
