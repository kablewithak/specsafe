# V3 Authoring Ledger

## Current boundary

- **Boundary:** V3 calibration workload-mix fixtures.
- **V3 calibration runtime inputs authored:** 36 of 36 cases.
- **V3 calibration expected outcomes authored:** 36 of 36 cases.
- **V3 calibration observations authored:** 144 of 144.
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
| `CRV3-CAL-CURVE-COVERAGE` | `CRV3-101` to `CRV3-112` | 12 | 48 | Fresh raw-confidence coverage for the fixed eight-group calibration method. |
| `CRV3-CAL-POSITION-SPREAD` | `CRV3-113` to `CRV3-124` | 12 | 48 | Fresh position-spread coverage across the fixed four-position V3 contract. |
| `CRV3-CAL-WORKLOAD-MIX` | `CRV3-125` to `CRV3-136` | 12 | 48 | Fresh workload-mix coverage across structured text, code, and open-ended chat. |

The complete calibration corpus now contains broad confidence coverage, deliberate position variation, and a controlled workload-dependent confidence shift. Runtime inputs retain only lawful pre-sample confidence and visible-prefix state. This is synthetic controlled evidence only, not a production claim.

## Still reserved and absent

| Split / family | Cases | Observations | Status |
|---|---:|---:|---|
| Final evaluation | 24 | 96 | Quarantined reservation only |
| Adversarial regression | 8 | 32 | Reserved, absent |

## Next authorisation

`v3-calibration-manifest-authoring`

The next authorised slice may freeze the completed V3 calibration corpus behind a deterministic calibration manifest. Final-evaluation and adversarial bytes remain absent and quarantined.
