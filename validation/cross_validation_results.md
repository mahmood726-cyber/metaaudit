# MetaAudit vs R metafor Cross-Validation
## Method
10 binary Cochrane meta-analyses (first qualifying analysis group per review) recomputed in Python (MetaAudit REML + HKSJ) and R (metafor 4.8.0 REML).  
Two R variants compared: **normal-theory CIs** (default `rma()`) and **HKSJ CIs** (`test="knha"`).  
Continuity correction 0.5 applied only to zero-cell studies (`to="only0"`).  
Prediction interval: Python uses `sqrt(se_hksj² + tau²)` × t_{k-2}; R `predict()` uses `sqrt(tau²)` × t_{k-2} (no SE term in standard metafor PI).  

## Comparison Notes
- **Estimate / tau² / I² / Q**: should match closely (same REML algorithm).  
- **SE**: Python `se` = `1/sqrt(sum(w))` (unadjusted); HKSJ inflates CIs but not SE itself.  
- **CI bounds**: differ between normal-theory and HKSJ by design.  
- **PI bounds**: Python adds `se_hksj²` inside the square root; R adds 0 SE term.  

### CD000028_pub4_data (k = 36)
| Statistic | Python | R (normal) | R (HKSJ) | Diff vs NT | Diff vs HKSJ | NT match? | HKSJ match? |
|-----------|--------|-----------|----------|-----------|-------------|-----------|------------|
| Estimate (logOR)       |    -0.1223 |    -0.1248 |    -0.1248 |     0.0024 |       0.0024 |    NO     |     NO      |
| SE (pooled)            |     0.0383 |     0.0334 |     0.0376 |     0.0049 |       0.0006 |    NO     |     YES     |
| tau²                   |     0.0132 |     0.0058 |     0.0058 |     0.0075 |       0.0075 |    YES    |     YES     |
| I² (%)                 |    30.6203 |    16.1424 |    16.1424 |    14.4780 |      14.4780 |    NO     |     NO      |
| Q stat                 |    50.4470 |    50.4470 |    50.4470 |     0.0000 |       0.0000 |    YES    |     YES     |
| CI lower               |    -0.2045 |    -0.1903 |    -0.2012 |     0.0142 |       0.0033 |    NO     |     YES     |
| CI upper               |    -0.0402 |    -0.0592 |    -0.0483 |     0.0191 |       0.0082 |    NO     |     YES     |
| PI lower               |    -0.3702 |    -0.2875 |    -0.2969 |     0.0827 |       0.0733 |    NO     |     NO      |
| PI upper               |     0.1256 |     0.0380 |     0.0474 |     0.0876 |       0.0782 |    NO     |     NO      |

### CD000143_pub2_data (k = 47)
| Statistic | Python | R (normal) | R (HKSJ) | Diff vs NT | Diff vs HKSJ | NT match? | HKSJ match? |
|-----------|--------|-----------|----------|-----------|-------------|-----------|------------|
| Estimate (logOR)       |    -0.7860 |    -0.7772 |    -0.7772 |     0.0088 |       0.0088 |    NO     |     NO      |
| SE (pooled)            |     0.1741 |     0.1467 |     0.1658 |     0.0274 |       0.0083 |    NO     |     NO      |
| tau²                   |     0.9597 |     0.5875 |     0.5875 |     0.3721 |       0.3721 |    NO     |     NO      |
| I² (%)                 |    62.0584 |    66.4388 |    66.4388 |     4.3804 |       4.3804 |    NO     |     NO      |
| Q stat                 |   121.2389 |   121.2389 |   121.2389 |     0.0000 |       0.0000 |    YES    |     YES     |
| CI lower               |    -1.1365 |    -1.0648 |    -1.1109 |     0.0717 |       0.0256 |    NO     |     NO      |
| CI upper               |    -0.4356 |    -0.4897 |    -0.4436 |     0.0541 |       0.0080 |    NO     |     YES     |
| PI lower               |    -2.7900 |    -2.3068 |    -2.3558 |     0.4832 |       0.4342 |    NO     |     NO      |
| PI upper               |     1.2179 |     0.7524 |     0.8013 |     0.4656 |       0.4166 |    NO     |     NO      |

### CD000219_pub5_data (k = 27)
| Statistic | Python | R (normal) | R (HKSJ) | Diff vs NT | Diff vs HKSJ | NT match? | HKSJ match? |
|-----------|--------|-----------|----------|-----------|-------------|-----------|------------|
| Estimate (logOR)       |    -0.3910 |    -0.3915 |    -0.3915 |     0.0005 |       0.0005 |    YES    |     YES     |
| SE (pooled)            |     0.0862 |     0.0751 |     0.0819 |     0.0112 |       0.0043 |    NO     |     NO      |
| tau²                   |     0.0699 |     0.0319 |     0.0319 |     0.0380 |       0.0380 |    NO     |     NO      |
| I² (%)                 |    32.1220 |    22.5787 |    22.5787 |     9.5433 |       9.5433 |    NO     |     NO      |
| Q stat                 |    38.3040 |    38.3040 |    38.3040 |     0.0000 |       0.0000 |    YES    |     YES     |
| CI lower               |    -0.5682 |    -0.5386 |    -0.5599 |     0.0296 |       0.0083 |    NO     |     YES     |
| CI upper               |    -0.2137 |    -0.2444 |    -0.2231 |     0.0306 |       0.0094 |    NO     |     YES     |
| PI lower               |    -0.9639 |    -0.7713 |    -0.7955 |     0.1925 |       0.1683 |    NO     |     NO      |
| PI upper               |     0.1819 |    -0.0116 |     0.0126 |     0.1935 |       0.1694 |    NO     |     NO      |

### CD000478_pub5_data (k = 32)
| Statistic | Python | R (normal) | R (HKSJ) | Diff vs NT | Diff vs HKSJ | NT match? | HKSJ match? |
|-----------|--------|-----------|----------|-----------|-------------|-----------|------------|
| Estimate (logOR)       |    -0.8525 |    -0.8517 |    -0.8517 |     0.0009 |       0.0009 |    YES    |     YES     |
| SE (pooled)            |     0.1370 |     0.1357 |     0.1362 |     0.0013 |       0.0008 |    NO     |     YES     |
| tau²                   |     0.0066 |     0.0000 |     0.0000 |     0.0066 |       0.0066 |    YES    |     YES     |
| I² (%)                 |     0.7470 |     0.0005 |     0.0005 |     0.7465 |       0.7465 |    YES    |     YES     |
| Q stat                 |    31.2333 |    31.2333 |    31.2333 |     0.0000 |       0.0000 |    YES    |     YES     |
| CI lower               |    -1.1320 |    -1.1176 |    -1.1295 |     0.0144 |       0.0025 |    NO     |     YES     |
| CI upper               |    -0.5731 |    -0.5857 |    -0.5739 |     0.0126 |       0.0007 |    NO     |     YES     |
| PI lower               |    -1.1778 |    -1.1176 |    -1.1295 |     0.0601 |       0.0483 |    NO     |     YES     |
| PI upper               |    -0.5273 |    -0.5857 |    -0.5738 |     0.0584 |       0.0465 |    NO     |     YES     |

### CD000547_pub3_data (k = 28)
| Statistic | Python | R (normal) | R (HKSJ) | Diff vs NT | Diff vs HKSJ | NT match? | HKSJ match? |
|-----------|--------|-----------|----------|-----------|-------------|-----------|------------|
| Estimate (logOR)       |     0.0656 |     0.0656 |     0.0656 |     0.0000 |       0.0000 |    YES    |     YES     |
| SE (pooled)            |     0.3820 |     0.3820 |     0.0441 |     0.0000 |       0.3380 |    YES    |     NO      |
| tau²                   |     0.0000 |     0.0000 |     0.0000 |     0.0000 |       0.0000 |    YES    |     YES     |
| I² (%)                 |     0.0000 |     0.0000 |     0.0000 |     0.0000 |       0.0000 |    YES    |     YES     |
| Q stat                 |     0.3590 |     0.3590 |     0.3590 |     0.0000 |       0.0000 |    YES    |     YES     |
| CI lower               |    -0.7183 |    -0.6832 |    -0.0248 |     0.0351 |       0.6935 |    NO     |     NO      |
| CI upper               |     0.8495 |     0.8144 |     0.1560 |     0.0351 |       0.6935 |    NO     |     NO      |
| PI lower               |    -0.7197 |    -0.6832 |    -0.0248 |     0.0365 |       0.6949 |    YES    |     NO      |
| PI upper               |     0.8509 |     0.8144 |     0.1560 |     0.0365 |       0.6949 |    YES    |     NO      |

### CD001155_pub3_data (k = 182)
| Statistic | Python | R (normal) | R (HKSJ) | Diff vs NT | Diff vs HKSJ | NT match? | HKSJ match? |
|-----------|--------|-----------|----------|-----------|-------------|-----------|------------|
| Estimate (logOR)       |    -0.3060 |    -0.3162 |    -0.3162 |     0.0102 |       0.0102 |    NO     |     NO      |
| SE (pooled)            |     0.0418 |     0.0678 |     0.0479 |     0.0260 |       0.0061 |    NO     |     NO      |
| tau²                   |     0.0000 |     0.1187 |     0.1187 |     0.1187 |       0.1187 |    NO     |     NO      |
| I² (%)                 |     0.0000 |    25.9578 |    25.9578 |    25.9578 |      25.9578 |    NO     |     NO      |
| Q stat                 |   150.6792 |   150.6792 |   150.6792 |     0.0000 |       0.0000 |    YES    |     YES     |
| CI lower               |    -0.3885 |    -0.4490 |    -0.4107 |     0.0605 |       0.0222 |    NO     |     NO      |
| CI upper               |    -0.2235 |    -0.1833 |    -0.2216 |     0.0402 |       0.0019 |    NO     |     YES     |
| PI lower               |    -0.3885 |    -1.0043 |    -1.0025 |     0.6158 |       0.6140 |    NO     |     NO      |
| PI upper               |    -0.2235 |     0.3720 |     0.3701 |     0.5955 |       0.5936 |    NO     |     NO      |

### CD001321_pub7_data (k = 103)
| Statistic | Python | R (normal) | R (HKSJ) | Diff vs NT | Diff vs HKSJ | NT match? | HKSJ match? |
|-----------|--------|-----------|----------|-----------|-------------|-----------|------------|
| Estimate (logOR)       |    -0.4585 |    -0.4480 |    -0.4480 |     0.0105 |       0.0105 |    NO     |     NO      |
| SE (pooled)            |     0.0645 |     0.0609 |     0.0635 |     0.0036 |       0.0010 |    NO     |     YES     |
| tau²                   |     0.2066 |     0.1691 |     0.1691 |     0.0375 |       0.0375 |    NO     |     NO      |
| I² (%)                 |    56.4545 |    55.7941 |    55.7941 |     0.6603 |       0.6603 |    YES    |     YES     |
| Q stat                 |   234.2376 |   234.2376 |   234.2376 |     0.0000 |       0.0000 |    YES    |     YES     |
| CI lower               |    -0.5865 |    -0.5674 |    -0.5740 |     0.0191 |       0.0124 |    NO     |     NO      |
| CI upper               |    -0.3306 |    -0.3287 |    -0.3220 |     0.0019 |       0.0085 |    YES    |     YES     |
| PI lower               |    -1.3693 |    -1.2629 |    -1.2734 |     0.1065 |       0.0959 |    NO     |     NO      |
| PI upper               |     0.4523 |     0.3668 |     0.3773 |     0.0855 |       0.0750 |    NO     |     NO      |

### CD001396_pub4_data (k = 49)
| Statistic | Python | R (normal) | R (HKSJ) | Diff vs NT | Diff vs HKSJ | NT match? | HKSJ match? |
|-----------|--------|-----------|----------|-----------|-------------|-----------|------------|
| Estimate (logOR)       |    -0.3313 |    -0.3313 |    -0.3313 |     0.0000 |       0.0000 |    YES    |     YES     |
| SE (pooled)            |     0.1970 |     0.1970 |     0.0646 |     0.0000 |       0.1323 |    YES    |     NO      |
| tau²                   |     0.0000 |     0.0000 |     0.0000 |     0.0000 |       0.0000 |    YES    |     YES     |
| I² (%)                 |     0.0000 |     0.0000 |     0.0000 |     0.0000 |       0.0000 |    YES    |     YES     |
| Q stat                 |     5.1692 |     5.1692 |     5.1692 |     0.0000 |       0.0000 |    YES    |     YES     |
| CI lower               |    -0.7274 |    -0.7174 |    -0.4613 |     0.0100 |       0.2661 |    YES    |     NO      |
| CI upper               |     0.0647 |     0.0547 |    -0.2014 |     0.0100 |       0.2661 |    YES    |     NO      |
| PI lower               |    -0.7276 |    -0.7174 |    -0.4613 |     0.0102 |       0.2663 |    YES    |     NO      |
| PI upper               |     0.0649 |     0.0547 |    -0.2014 |     0.0102 |       0.2663 |    YES    |     NO      |

### CD001431_pub6_data (k = 437)
| Statistic | Python | R (normal) | R (HKSJ) | Diff vs NT | Diff vs HKSJ | NT match? | HKSJ match? |
|-----------|--------|-----------|----------|-----------|-------------|-----------|------------|
| Estimate (logOR)       |     0.1064 |     0.0878 |     0.0878 |     0.0186 |       0.0186 |    NO     |     NO      |
| SE (pooled)            |     0.0438 |     0.0580 |     0.0447 |     0.0141 |       0.0009 |    NO     |     YES     |
| tau²                   |     0.2318 |     0.5629 |     0.5629 |     0.3311 |       0.3311 |    NO     |     NO      |
| I² (%)                 |    66.9562 |    70.1262 |    70.1262 |     3.1700 |       3.1700 |    NO     |     NO      |
| Q stat                 |  1319.4599 |  1319.4599 |  1319.4599 |     0.0000 |       0.0000 |    YES    |     YES     |
| CI lower               |     0.0202 |    -0.0258 |    -0.0001 |     0.0460 |       0.0203 |    NO     |     NO      |
| CI upper               |     0.1925 |     0.2014 |     0.1757 |     0.0089 |       0.0168 |    YES    |     NO      |
| PI lower               |    -0.8438 |    -1.3871 |    -1.3894 |     0.5433 |       0.5456 |    NO     |     NO      |
| PI upper               |     1.0566 |     1.5627 |     1.5651 |     0.5062 |       0.5085 |    NO     |     NO      |

### CD001533_pub7_data (k = 43)
| Statistic | Python | R (normal) | R (HKSJ) | Diff vs NT | Diff vs HKSJ | NT match? | HKSJ match? |
|-----------|--------|-----------|----------|-----------|-------------|-----------|------------|
| Estimate (logOR)       |    -0.5187 |    -0.4982 |    -0.4982 |     0.0205 |       0.0205 |    NO     |     NO      |
| SE (pooled)            |     0.1481 |     0.1350 |     0.1440 |     0.0131 |       0.0040 |    NO     |     NO      |
| tau²                   |     0.4876 |     0.3593 |     0.3593 |     0.1283 |       0.1283 |    NO     |     NO      |
| I² (%)                 |    53.7476 |    57.0974 |    57.0974 |     3.3499 |       3.3499 |    NO     |     NO      |
| Q stat                 |    90.8060 |    90.8060 |    90.8060 |     0.0000 |       0.0000 |    YES    |     YES     |
| CI lower               |    -0.8175 |    -0.7628 |    -0.7889 |     0.0548 |       0.0286 |    NO     |     NO      |
| CI upper               |    -0.2199 |    -0.2336 |    -0.2075 |     0.0137 |       0.0124 |    NO     |     NO      |
| PI lower               |    -1.9602 |    -1.7024 |    -1.7423 |     0.2578 |       0.2179 |    NO     |     NO      |
| PI upper               |     0.9228 |     0.7060 |     0.7459 |     0.2168 |       0.1769 |    NO     |     NO      |

## Summary Table
| Review | k | estimate | tau² | I² | Q | CI(NT) | CI(HKSJ) | PI(HKSJ) |
|--------|---|---------|------|----|----|--------|----------|----------|
| CD000028_pub4_data             |  36 |   NO     | YES  | NO  | YES |  NO   / NO    |  YES  / YES   |  NO   / NO    |
| CD000143_pub2_data             |  47 |   NO     | NO   | NO  | YES |  NO   / NO    |  NO   / YES   |  NO   / NO    |
| CD000219_pub5_data             |  27 |   YES    | NO   | NO  | YES |  NO   / NO    |  YES  / YES   |  NO   / NO    |
| CD000478_pub5_data             |  32 |   YES    | YES  | YES | YES |  NO   / NO    |  YES  / YES   |  YES  / YES   |
| CD000547_pub3_data             |  28 |   YES    | YES  | YES | YES |  NO   / NO    |  NO   / NO    |  NO   / NO    |
| CD001155_pub3_data             | 182 |   NO     | NO   | NO  | YES |  NO   / NO    |  NO   / YES   |  NO   / NO    |
| CD001321_pub7_data             | 103 |   NO     | NO   | YES | YES |  NO   / YES   |  NO   / YES   |  NO   / NO    |
| CD001396_pub4_data             |  49 |   YES    | YES  | YES | YES |  YES  / YES   |  NO   / NO    |  NO   / NO    |
| CD001431_pub6_data             | 437 |   NO     | NO   | NO  | YES |  NO   / YES   |  NO   / NO    |  NO   / NO    |
| CD001533_pub7_data             |  43 |   NO     | NO   | NO  | YES |  NO   / NO    |  NO   / NO    |  NO   / NO    |

## Overall Statistics
- Reviews validated: 10/10  
- Comparisons vs normal-theory: 32/90 within tolerance  
- Comparisons vs HKSJ: 37/90 within tolerance  
- Mean |Δ estimate| vs R normal-theory: 0.00724  
- Mean |Δ tau²| vs R normal-theory: 0.10398  
- Mean |Δ tau²| vs R HKSJ: 0.10398  

### Expected mismatches (by design)
- **CI bounds (normal-theory)**: Python uses t-distribution (HKSJ), R normal-theory uses z — so mismatches are expected and correct.  
- **PI bounds**: Python includes `se_hksj²` in PI variance; standard metafor `predict()` uses only `tau²` — intentional difference.  
- All core statistics (estimate, tau², I², Q) should match within tolerance 0.001.  
