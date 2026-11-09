# EQ-REAL-001 validation plan — DRAFT, NOT FROZEN

**Do not open or score any reserved municipality's 2026 second-round four-count outcomes until this document is finalised, versioned and frozen.**

Primary external split: municipalities withheld as whole clusters; all their sections and both rounds remain together. Exclude municipalities previously viewed in earlier REL-RN and EQ-CMP-RN analyses from the new untouched test. Determine and publish this list from recovered source code/records, not recollection. Fix random seed, municipality IDs, UF/region blocking, assignment symmetry, search grammar, predictors and information dates.

Regimes:
1. Known C2 (conditional-composition allocation, *not* fully prospective).
2. Predicted C2 and four-category shares (fully prospective).

Target error per category K: `100 * |sum_s(predicted_K - observed_K)| / actual_C2_m` percentage points, with separate zero-denominator handling. Record per-section MAE, signed bias, total absolute error, interval coverage/sharpness, across-municipality uncertainty and proper scoring metrics where possible.

High-precision benchmark retained without alteration: W/L each ≤0.50 percentage points; blank/null each ≤0.10 percentage points; section-level four-category absolute-error sum at least 10% below the strongest legitimate no-transformation comparator for the same prediction regime. Initial benchmark passes ≥4 of 5 *predesignated* municipalities only when all five conditions are met.

Additional classifications:
- *Exploratory*: reproducible mathematical relation; no independent superiority claimed.
- *Promising*: development/internal holdout evidence against appropriately flexible no-transformation behavioural baselines. Provisional numerical thresholds to be calibrated; **not defined yet**.
- *Validated predictive improvement*: frozen independent external test demonstrates out-of-sample superiority to strongest baseline, with clustered uncertainty and multiplicity accounted for.
- *High precision*: all original five numeric requirements fulfilled on the designated independent test.

Calibration can use 2022/historical data, outside behavioural evidence and targeted synthetic procedure checks without inspecting reserved 2026 test targets. Calibration must account for the entire search-selection pipeline and previously observed failure under behavioural shift. Do not revise external pass criteria after external scores are observed.

This plan remains DRAFT because raw-source recovery, prior-exposure audit and external municipality list are incomplete.


## Historical-data audit update — 9 November 2026

The actual 2022 RN presidential ballot bulletins and nationwide 2022 presidential section data have been obtained and cross-reconciled, as has the 2026 nationwide presidential archive against the RN pilot. Their uploaded-byte SHA-256 values are recorded in the source manifest and audit report. The 2022 RN section dataset contains 7,674 two-round keys, and 7,565 section identifiers overlap with the 2026 RN pilot, subject to polling-place and electorate changes.

**External-data firewall:** all 2026 RN second-round counts have been inspected for provenance/aggregate auditing, and historical RN model exposure records remain unresolved. Treat RN as an exposed development/audit region for the purposes of fresh external validation. For a genuinely external 2026 test, reserve municipalities outside RN using a deterministic predeclared procedure, document municipality/UF IDs and temporal exposure history, then forbid reads of the second-round target values until equations and classification thresholds are frozen. The mere presence of all-national 2026 ZIP bytes in storage does not by itself license use of those reserved target counts.

The exploratory and promising numerical thresholds remain **unfrozen**; no empirical equation or reserved-outcome validation has been run. The original high-precision thresholds are unchanged.
