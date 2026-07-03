# V3 Authoring Ledger

## Current boundary

- **Boundary:** V3 calibration position-spread fixtures.
- **V3 calibration runtime inputs authored:** 24 of 36 cases.
- **V3 calibration expected outcomes authored:** 24 of 36 cases.
- **V3 calibration observations authored:** 96 of 144.
- **V3 final-evaluation runtime inputs authored:** no.
- **V3 final-evaluation expected outcomes authored:** no.
- **V3 adversarial-regression runtime inputs authored:** no.
- **V3 adversarial-regression expected outcomes authored:** no.
- **V3 manifests authored:** no.
- **V3 calibration fit authored:** no.
- **V3 policy or scheduler code authored:** no.
- **V1/V2 data-bearing evidence used:** no.

## Authored families

| Family | Case IDs | Cases | Observations | Purpose |
|---|---|---:|---:|---|
| `CRV3-CAL-CURVE-COVERAGE` | `CRV3-101` to `CRV3-112` | 12 | 48 | Fresh raw-confidence coverage for the future fixed eight-group calibration method. |
| `CRV3-CAL-POSITION-SPREAD` | `CRV3-113` to `CRV3-124` | 12 | 48 | Fresh position-spread coverage across the fixed four-position V3 contract. |

The first family supplies broad raw-confidence coverage. The second supplies deliberate position variation: observed conditional acceptance declines from position one through position four while runtime inputs retain only lawful pre-sample confidence and visible-prefix state. This is synthetic controlled evidence only, not a production claim.

## Still reserved and absent

| Split / family | Cases | Observations | Status |
|---|---:|---:|---|
| Calibration workload mix | 12 | 48 | Reserved, absent |
| Final evaluation | 24 | 96 | Quarantined reservation only |
| Adversarial regression | 8 | 32 | Reserved, absent |

## Next authorisation

`v3-calibration-workload-mix-fixture-authoring`

Only calibration case pairs `CRV3-125` through `CRV3-136` may be authored next. Final-evaluation and adversarial bytes remain absent and quarantined.
