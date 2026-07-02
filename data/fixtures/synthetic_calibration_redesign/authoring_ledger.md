# Calibration Redesign Fixture Authoring Ledger

## Status

```text
fixture_set_id=synthetic-calibration-redesign-v1
fixture_set_version=1.0.0
status=registry-governed; case-assets-not-yet-authored
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
| Retain runtime inputs and expected outcomes as future separate assets. | The runtime boundary must not expose observed labels. | Preserves causal replay discipline. |

## Explicit exclusions

- `STF-004` is historical evidence only. It must not appear in this fixture set, registry, manifest, inputs, outcomes, fit selection, or final assessment selection.
- No case outcome values are authored in this governance slice.
- No calibration artifact, threshold, policy action, capacity profile, utility scorer, or report is created here.

## Next authoring gate

Before any case asset is created, preserve the assigned case ID, split, scenario family, and source-template fingerprint exactly as registered. Any proposed change requires a reviewed governance update before authoring proceeds.
