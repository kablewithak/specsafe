# V4 Authoring Ledger

## Current stage

`final_evaluation_fixtures_authored`

## Authoring record

| Artifact class | Status | Evidence role |
|---|---|---|
| V4 scenario-family registry | Updated | Current-stage metadata, frozen calibration provenance carry-forward, and complete reservation |
| Curve-coverage runtime/outcome pairs, CRV4-101 through CRV4-112 | Authored | Calibration-only evidence |
| Position-spread runtime/outcome pairs, CRV4-113 through CRV4-124 | Authored | Calibration-only evidence |
| Workload-mix runtime/outcome pairs, CRV4-125 through CRV4-136 | Authored | Calibration-only evidence |
| Capacity-contrast runtime/outcome pairs, CRV4-137 through CRV4-148 | Authored | Calibration-only evidence |
| Calibration manifest | Frozen | Immutable 96-asset calibration provenance and integrity boundary |
| Regularized-isotonic calibration artifact | Authored | Calibration-only monotonic confidence map |
| Regularized-isotonic fit report | Authored | Fit-data diagnostics; held-out gate not assessed |
| Final runtime/outcome pairs, CRV4-201 through CRV4-236 | Authored | Quarantined held-out evidence; no final manifest or scoring |
| Adversarial runtime inputs and outcomes | Not authored | Quarantined regression evidence |
| Final manifest, index, and held-out result | Not authored | Next freeze boundary and later one-time evidence |

## Integrity statement

The 48 calibration-only case pairs remain protected by their immutable 96-asset manifest.
Thirty-six final-evaluation runtime/outcome pairs now exist only in the separate
`final_evaluation/` tree. Their runtime assets contain no acceptance label, prefix-survival
label, or current candidate token. The final assets are not yet governed by a final manifest,
and no held-out metric, policy, baseline, or runtime claim is made at this stage.
