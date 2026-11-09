# First observed-data behavioural reference — 2022 RN, known-turnout regime

This is a deliberately simple **no-hypothetical-transformation baseline**, not an equation discovery, not a 2026 forecast, and not a previously unseen test. Uses 7,674 official 2022 RN presidential section records for both rounds, derived from the supplied BU ZIPs and independently reconciled at section/category level against the nationwide presidential section archive.

For a section with first-round finalists `w1,l1`, eliminated candidates `o1`, blank `b1`, null `n1`, conditional on actual second-round turnout `C2`, assign weights

```
w = (w1+l1+o1)*w1/(w1+l1)
l = (w1+l1+o1)*l1/(w1+l1)
b = b1
n = n1
```

and scale these weights proportionally to `C2`, using deterministic Hamilton largest-remainder allocation to give non-negative integers that conserve `C2` exactly. Zero-finalist and zero-first-round-turnout cases use explicitly specified neutral fallback. Under this reference, first-round blank/null rates persist, while eliminated-candidate votes are distributed in the observed first-round finalist ratio. The reference should be compared with more flexible no-transformation models later.

**Actual executed results (not simulations):**

| Metric | Observed 2022 RN reference |
|---|---:|
| Sections | 7,674 |
| Municipalities | 167 |
| Sum of section-level four-category absolute count errors | **116,490** |
| Mean four-category absolute error per section | **15.1798 votes** |
| Mean per-category absolute error per section | **3.7950 votes** |
| Municipalities satisfying *all four* high-precision category accuracy bounds alone | **0 / 167** |

The original high-precision benchmark also requires ≥10% improvement against the strongest legitimate no-transformation comparator; **that fifth condition cannot be claimed for this model because it is itself a baseline**. Do not interpret 0/167 as a discovery failure or as a threshold calibration result. This exercise illustrates that extremely narrow municipal tolerances cannot be used as the only success definition and that behavioural reference selection matters. Exploratory/promising thresholds remain provisional and unfrozen.

Reproduce from `rn_presidential_sections_2022.csv`:

```sh
python3 src/continuity_baseline_2022.py --2022-sections rn_presidential_sections_2022.csv --municipal-csv rn_2022_baseline_municipal.csv --summary rn_2022_baseline.json
```

**Limitations:** conditional on observed 2022 C2, no prospective turnout forecast; no fitting/hyperparameter tuning; no second baseline yet; no interval calibration, regional holdout or external validation; does not support any inference about how the official counts were generated.
