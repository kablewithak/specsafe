# V4 Authoring Ledger

## Current stage

`calibration_workload_mix_authored`

## Authoring record

| Artifact class | Status | Evidence role |
|---|---|---|
| V4 scenario-family registry | Updated | Reservation and active-boundary metadata |
| Curve-coverage runtime inputs, CRV4-101 through CRV4-112 | Authored | Calibration-only decision-time inputs |
| Curve-coverage expected outcomes, CRV4-101 through CRV4-112 | Authored | Calibration-only post-hoc labels |
| Position-spread runtime inputs, CRV4-113 through CRV4-124 | Authored | Calibration-only decision-time inputs |
| Position-spread expected outcomes, CRV4-113 through CRV4-124 | Authored | Calibration-only post-hoc labels |
| Workload-mix runtime inputs, CRV4-125 through CRV4-136 | Authored | Calibration-only decision-time inputs |
| Workload-mix expected outcomes, CRV4-125 through CRV4-136 | Authored | Calibration-only post-hoc labels |
| Capacity-contrast calibration case pairs | Not authored | Future fitting-only evidence |
| Final runtime inputs and outcomes | Not authored | Quarantined final-evaluation evidence |
| Adversarial runtime inputs and outcomes | Not authored | Quarantined regression evidence |
| Calibration manifest | Not authored | Future immutable calibration provenance |
| Calibration artifact and fit report | Not authored | Future frozen calibration output |
| Final manifest, index, and held-out result | Not authored | Future one-time final evidence |

## Integrity statement

Exactly thirty-six calibration-only runtime/outcome case pairs exist. Their runtime inputs
contain no acceptance label, prefix-survival label, or current candidate token. Their expected
outcomes remain in separate files. No final-evaluation or adversarial case byte exists in this
fixture root.
