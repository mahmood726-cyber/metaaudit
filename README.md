# MetaAudit

**A full-spectrum computational audit of 6,229 Cochrane meta-analyses.**

MetaAudit applies eleven pre-specified automated detectors to 6,229 pairwise meta-analyses from 501 Cochrane systematic reviews, all recomputed from study-level data in the Pairwise70 dataset. The pipeline is fully deterministic and openly released.

## Headline findings

- **29.5%** of the 6,229 meta-analyses failed at least one detector at FAIL or CRITICAL severity
- **3.1%** failed three or more
- **77.6%** of the 501 reviews contained at least one failing meta-analysis
- Most prevalent flaws (among applicable MAs): publication bias **37.2%** (k ≥ 10), model misspecification **15.1%**, prediction gap **11.2%**
- Strongest co-occurrence: model misspecification × excess significance (φ = 0.384)

One meta-analysis accumulated six simultaneous flaw flags.

## The eleven detectors

| # | Detector | Severity lattice | Module |
|---|---|---|---|
| 1 | Underpowered | k, OIS, post-hoc power | `detectors/underpowered.py` |
| 2 | Publication bias | Egger + Begg + trim-and-fill | `detectors/pub_bias.py` |
| 3 | Model misspecification | FE-vs-RE, I² thresholds | `detectors/model_misspec.py` |
| 4 | Small-study effects | Peters / Spearman | `detectors/small_study.py` |
| 5 | Prediction-interval gap | CI significant, PI spans null | `detectors/prediction_gap.py` |
| 6 | Excess significance | Ioannidis–Trikalinos | `detectors/excess_sig.py` |
| 7 | Fragility index | Walsh et al. minimum-flip | `detectors/fragility.py` |
| 8 | Overclaiming | Effect vs CI vs stated conclusion | `detectors/overclaiming.py` |
| 9 | Data integrity | Benford + GRIM-like + SPRITE checks | `detectors/integrity.py` |
| 10 | Study overlap | Shared primary studies across MAs | `detectors/overlap.py` |
| 11 | Certainty mismatch | GRADE certainty vs computational flags | `detectors/certainty_mismatch.py` |

Each detector classifies a meta-analysis as `PASS`, `WARN`, `FAIL`, `CRITICAL`, or `INSUFFICIENT_DATA`.

## Architecture

```
metaaudit/
├── loader.py       # Pairwise70 RDA → study-level DataFrame
├── recompute.py    # Recompute pooled effects (REML + HKSJ)
├── detectors/      # 11 independent detector modules
├── severity.py     # Classify detector output → severity
├── correlator.py   # Flaw co-occurrence (phi coefficients)
└── export.py       # JSON + CSV outputs for dashboard/paper
```

Command-line entry point `run_audit.py` runs the full pipeline end-to-end and emits:

- `results/audit_results.json` — per-MA detector outputs (20 MB)
- `results/audit_results.csv` — flat table for downstream analysis (7 MB)
- `results/prevalence.csv` — flaw prevalence by detector
- `results/cooccurrence.csv` — pairwise phi coefficients

## Requirements

- Python ≥ 3.11
- numpy ≥ 1.24, scipy ≥ 1.10, pandas ≥ 2.0, pyreadr (for RDA loading)
- Pairwise70 dataset (RDA files) — contact the authors; not redistributed here

## Reproducing the headline numbers

```bash
# from repo root
python -m pytest tests/                 # default regression and data contracts
python run_audit.py --data PATH/TO/pairwise70  # full audit (~20 minutes)
python build_dashboard.py               # generates dashboard/index.html
```

## Testing

- Run `python -m pytest -q` for current test results; external-data and browser checks declare their prerequisites.
- One test per detector, plus integration, loader, recompute, severity, correlator, export, and path-handling tests

## Citation

See `paper/metaaudit_bmj_main.md` for the full manuscript. Interim citation:

> Ahmad M. MetaAudit: A computational full-spectrum audit of 6,229 Cochrane meta-analyses reveals pervasive methodological flaws. Manuscript, 2026.

## Related work in the portfolio

MetaAudit is the **Layer-2 audit engine** in the evidence-intelligence stack described in the [portfolio manifesto](https://github.com/mahmood726-cyber/). Downstream tools that consume MetaAudit output include:

- [EvidenceOracle](https://github.com/mahmood726-cyber/EvidenceOracle) — ML prediction of MA overturn
- [ContradictionMap](https://github.com/mahmood726-cyber/ContradictionMap) — cross-review contradictions
- [ActionableEvidence](https://github.com/mahmood726-cyber/ActionableEvidence) — GO/NO-GO verdict including audit clean-run as a gate

## License

MIT — see `LICENSE`.

## Author

Mahmood Ahmad (mahmood.ahmad2@nhs.net, ORCID `0009-0003-7781-4478`), Tahir Heart Institute.

### Dashboard builder inputs

`python build_dashboard.py` requires `results/dashboard_data.json` from the
audit pipeline and `dashboard/index.template.html`. Importing the builder does
not read inputs or rebuild files. Use `--data`, `--template`, and `--output`
for explicit locations. Missing inputs, invalid JSON (including non-finite
values), or a template without exactly one data marker fail before replacing
an existing dashboard. JSON text is escaped for embedding in an HTML script.

For the browser contract, install `playwright` and run `python -m playwright
install chromium`, then set `RUN_BROWSER_TESTS=1` and run
`python -m pytest tests/test_ui.py -q`. It builds a temporary page from the
committed dashboard snapshot and tests navigation and filtering at
`http://127.0.0.1:8000/`.
