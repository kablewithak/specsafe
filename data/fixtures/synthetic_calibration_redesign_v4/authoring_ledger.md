# V4 Evidence Authoring Ledger

## Current stage

`final_evaluation_manifest_frozen`

## Authoring record

| Artifact class | Status | Evidence role |
|---|---|---|
| V4 scenario-family registry | Updated | Active-stage metadata and carried-forward frozen provenance |
| Calibration runtime/outcome pairs, CRV4-101 through CRV4-148 | Frozen | Calibration-only evidence |
| Calibration manifest | Frozen | Immutable 96-asset calibration inventory |
| Regularized-isotonic calibration artifact | Authored | Calibration-only monotonic confidence map |
| Regularized-isotonic fit report | Authored | Fit-data diagnostics; held-out gate not assessed |
| Final runtime/outcome pairs, CRV4-201 through CRV4-236 | Frozen | Quarantined held-out evidence |
| Final-evaluation manifest | Frozen | Immutable 72-asset held-out inventory |
| Final-evidence index | Frozen | Deterministic case, trace, workload, and capacity provenance |
| Held-out assessment result | Not authored | Next write-once final calibration evidence |
| Adversarial runtime inputs and outcomes | Not authored | Quarantined regression evidence |
| Scheduler, baselines, and replay scorer | Not authored | Blocked until the complete held-out calibration gate passes |

## Integrity statement

The 48 calibration case pairs remain protected by their immutable 96-asset manifest. The 36 final
case pairs remain in a separate held-out tree and are protected by a 72-asset final manifest plus a
label-free final-evidence index. Runtime assets never contain candidate token IDs, observed
acceptance labels, or prefix-survival labels. No held-out metric or policy claim exists yet.

## Next authorized boundary

`v4-final-heldout-calibration-assessment`
