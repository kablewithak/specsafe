# Calibration Redesign Fixture Authoring Ledger

## Status

```text
fixture_set_id=synthetic-calibration-redesign-v1
fixture_set_version=1.0.0
status=registry-governed; calibration-corpus-frozen; calibration-artifact-fitted; final-mixed-reliability-authored; final-abrupt-suffix-pending
candidate_calibrator=logit-temperature-scaling-v1
historical_heldout_case=STF-004 permanently excluded
```

## Accepted design decisions

| Decision | Reason | Evidence boundary preserved |
|---|---|---|
| Reserve `CRV1-001` through `CRV1-012` before case authoring. | IDs can be reviewed before runtime inputs or outcomes exist. | Prevents final-evaluation reshuffling after fitting. |
| Use two calibration families with three cases each. | Meets the governed diagnostic floor for fresh fitting evidence. | Calibration has no dependence on `STF-004`. |
| Use two quarantined final-evaluation families with two cases each. | Meets the governed held-out floor while keeping independent scenario templates. | Final evidence remains separate from fitting. |
| Store source-template fingerprints in the registry. | Makes family-level leakage testable instead of relying on filename conventions. | Blocks cross-split template reuse. |
| Retain runtime inputs and expected outcomes as separate assets. | The runtime boundary must not expose observed labels. | Preserves causal replay discipline. |
| Author `CRV1-009` and `CRV1-010` only under the predeclared `CRV1-FINAL-MIXED-RELIABILITY` family. | The family was registered as final evaluation and quarantined before any case bytes existed. | Prevents a calibration case from being relabelled as held-out evidence. |
| Keep `CRV1-009` and `CRV1-010` outside the fitted artifact's case list. | The temperature scaler is calibration-only and must remain frozen while final evidence is authored. | Blocks final-evaluation access and refitting. |

## Final mixed-reliability authoring record

| Case | Workload | Trace intent | Quarantine condition |
|---|---|---|---|
| `CRV1-009` | Structured text | Mixed reliability with a high-confidence rejection after an earlier rejected position. | Runtime input excludes candidate IDs and observed labels; outcomes stay post-hoc. |
| `CRV1-010` | Open-ended chat | Mixed reliability with a low-confidence rejection and later accepted token after prefix failure. | Runtime input excludes candidate IDs and observed labels; outcomes stay post-hoc. |

## Explicit exclusions

- `STF-004` is historical evidence only. It must not appear in this fixture set, registry, manifest, inputs, outcomes, fit selection, or final assessment selection.
- `CRV1-009` and `CRV1-010` must not be added to any calibration manifest, fitting selection, temperature-search routine, threshold selection, or policy configuration.
- No final-evaluation manifest, held-out calibration score, promotion decision, adaptive policy, capacity profile, utility scorer, or report is created in this slice.
- `CRV1-FINAL-ABRUPT-SUFFIX` remains unauthored and unavailable to all current code paths.

## Next authoring gate

Before authoring `CRV1-011` or `CRV1-012`, retain their registered family, split, data role, quarantine state, and source-template fingerprint. After both final families exist, create a separate final-evaluation manifest and loader boundary before any held-out calibration assessment.
