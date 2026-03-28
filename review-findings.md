# REVIEW CLEAN — All P0 and P1 fixed
### Date: 2026-03-28
### Summary: 5 P0 [FIXED], 8 P1 [FIXED], 5 P2 (from Statistical Methodologist + Software Engineer)

## P0 — Critical

- **P0-1** [Stats+SWE]: REML iteration is actually Paule-Mandel, not true REML Fisher scoring. Denominator `sum(w^2)` should be `sum(w^2) - sum(w^3)/sum(w)`. Peer reviewers will catch this. (`recompute.py:77`)
  - Fix: Implement true REML Fisher scoring or relabel as PM

- **P0-2** [Stats]: Prediction interval uses unadjusted SE instead of HKSJ-adjusted SE. PI may be too narrow when HKSJ inflates SE, inflating Module 1 false positives. (`recompute.py:131,217`)
  - Fix: Use `se_hksj` in PI computation

- **P0-3** [Stats+SWE]: Fragility index can get stuck on capped cells, returning inflated MAFI. Also modifies arm with fewest events globally instead of per-study optimal. (`fragility.py:57-77`)
  - Fix: Break on stale data, pick modification that maximally reduces |estimate|

- **P0-4** [SWE]: `_reml_tau2` silently returns unconverged tau2 if max_iter hit. Bad tau2 propagates to all 11 detectors. (`recompute.py:71-82`)
  - Fix: Return convergence flag, fall back to DL if unconverged

- **P0-5** [SWE]: `compute_smd` division by zero when both arms have n=1 (n_total-2=0). (`recompute.py:44-56`)
  - Fix: Guard df >= 1, return NaN for n_total < 3

## P1 — Important

- **P1-1** [Stats]: Hedges' g variance denominator should be `2*(n_total-3.4)` not `2*n_total`. ~10% underestimate for small studies. (`recompute.py:55`)
- **P1-2** [Stats]: Egger's test uses non-standard triple-weighting (1/se^3). P-values differ from metafor/meta. (`pub_bias.py:19-48`)
- **P1-3** [Stats]: Begg's test uses unadjusted residuals. Anti-conservative p-values. (`pub_bias.py:51-65`)
- **P1-4** [Stats]: Trim-and-fill uses FE weights in RE context. L0 estimator is non-standard. (`pub_bias.py:68-126`)
- **P1-5** [Stats]: "Peters' test" actually regresses on 1/SE not 1/N. Mislabeled. (`small_study.py:18-31`)
- **P1-6** [SWE]: Overlap index O(MAs * R^2) = 780M lookups. Cache per review. (`overlap.py, run_audit.py`)
- **P1-7** [SWE]: prevalence.json written with NaN (invalid JSON). Use SafeEncoder. (`run_audit.py:147`)
- **P1-8** [SWE]: ReviewData stores full df + sliced copies = 2x memory. (`loader.py:68-77`)

## P2 — Minor

- **P2-1** [Stats]: `opposite_extent > 0.1` threshold is scale-dependent (OK for logOR, wrong for MD)
- **P2-2** [Stats]: k=1 CI uses z=1.96 vs t-distribution for k>=2 (inconsistent)
- **P2-3** [SWE]: GIV overclaiming uses arbitrary 0.1 MCID. Should return insufficient_data.
- **P2-4** [SWE]: certainty_mismatch always receives None — dead detector in pipeline
- **P2-5** [SWE]: split_by_analysis .iloc[0] crashes on empty DataFrame

## False Positive Watch
- DOR = exp(mu1 + mu2) IS correct
- Clayton copula theta = 2*tau/(1-tau) IS correct
- Clopper-Pearson alpha/2 IS correct
