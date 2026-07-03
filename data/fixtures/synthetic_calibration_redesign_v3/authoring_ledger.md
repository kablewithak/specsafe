# V3 Authoring Ledger

## Current boundary

- **Boundary:** V3 calibration curve-coverage fixtures.
- **V3 calibration runtime inputs authored:** 12 of 36 cases.
- **V3 calibration expected outcomes authored:** 12 of 36 cases.
- **V3 calibration observations authored:** 48 of 144.
- **V3 final-evaluation runtime inputs authored:** no.
- **V3 final-evaluation expected outcomes authored:** no.
- **V3 adversarial-regression runtime inputs authored:** no.
- **V3 adversarial-regression expected outcomes authored:** no.
- **V3 manifests authored:** no.
- **V3 calibration fit authored:** no.
- **V3 policy or scheduler code authored:** no.
- **V1/V2 data-bearing evidence used:** no.

## Authored family

| Family | Case IDs | Cases | Observations | Purpose |
|---|---|---:|---:|---|
| `CRV3-CAL-CURVE-COVERAGE` | `CRV3-101` to `CRV3-112` | 12 | 48 | Fresh raw-confidence coverage for the future fixed eight-group calibration method. |

The observations cover four raw-confidence bands. Their labels intentionally form a monotonic but non-linear relationship so the future calibration method has a diagnostic curve to learn. This is synthetic controlled evidence only, not a production claim.

## Still reserved and absent

| Split / family | Cases | Observations | Status |
|---|---:|---:|---|
| Calibration position spread | 12 | 48 | Reserved, absent |
| Calibration workload mix | 12 | 48 | Reserved, absent |
| Final evaluation | 24 | 96 | Quarantined reservation only |
| Adversarial regression | 8 | 32 | Reserved, absent |

## Next authorisation

`v3-calibration-position-spread-fixture-authoring`

Only calibration case pairs `CRV3-113` through `CRV3-124` may be authored next. Final-evaluation and adversarial bytes remain absent and quarantined.
