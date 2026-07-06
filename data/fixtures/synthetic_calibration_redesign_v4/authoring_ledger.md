# V4 Authoring Ledger

## Current stage

`calibration_fit_diagnostics_complete`

## Authoring record

| Artifact class | Status | Evidence role |
|---|---|---|
| V4 scenario-family registry | Updated | Active-stage metadata, frozen provenance carry-forward, and complete reservation |
| Curve-coverage runtime/outcome pairs, CRV4-101 through CRV4-112 | Authored | Calibration-only evidence |
| Position-spread runtime/outcome pairs, CRV4-113 through CRV4-124 | Authored | Calibration-only evidence |
| Workload-mix runtime/outcome pairs, CRV4-125 through CRV4-136 | Authored | Calibration-only evidence |
| Capacity-contrast runtime/outcome pairs, CRV4-137 through CRV4-148 | Authored | Calibration-only evidence |
| Calibration manifest | Frozen | Immutable 96-asset provenance and integrity boundary |
| Regularized-isotonic calibration artifact | Authored | Calibration-only monotonic confidence map |
| Regularized-isotonic fit report | Authored | Fit-data diagnostics; held-out gate not assessed |
| Final runtime inputs and outcomes | Not authored | Quarantined final-evaluation evidence |
| Adversarial runtime inputs and outcomes | Not authored | Quarantined regression evidence |
| Final manifest, index, and held-out result | Not authored | Future one-time final evidence |

## Integrity statement

Exactly forty-eight calibration-only runtime/outcome case pairs exist. Their runtime inputs
contain no acceptance label, prefix-survival label, or current candidate token. The frozen
calibration manifest records each of the 96 asset hashes and byte counts, plus one aggregate
hash. The current registry carries forward both the frozen registry hash and manifest hash,
then anchors the external artifact and report hashes. A changed, missing, extra, or swapped
calibration asset blocks manifest verification. No final-evaluation or adversarial case byte
exists in this fixture root.
