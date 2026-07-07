# V5 Authoring Ledger

## Ledger status

```text
fixture_set_id=synthetic-calibration-successor-v5
registry_status=final_workload_variation_authored
calibration_runtime_input_assets=48
calibration_expected_outcome_assets=48
calibration_observations_frozen=192
calibration_manifest=frozen
calibration_artifact=retained
fit_diagnostics=retained
final_evaluation_runtime_input_assets=27
final_evaluation_expected_outcome_assets=27
final_evaluation_observations_authored=108
final_evaluation_manifest=absent
heldout_result=absent
```

## Evidence record

`CSV5-101..CSV5-148` remain frozen calibration-only case pairs. Their manifest, calibration
artifact, and diagnostics are unchanged. The three held-out families, `CSV5-201..CSV5-227`, are
self-authored synthetic curve-coverage, position-spread, and workload-variation evidence. They
are stored under `final_evaluation/` so they cannot enter calibration asset discovery or the
calibration manifest.

Runtime inputs contain decision-time scheduler context only. Candidate token identifiers,
acceptance labels, and prefix-survival labels remain physically separate in expected-outcome
assets. The final assets are not a final-evaluation manifest and do not establish a held-out
calibration result.

## Evidence boundary

No final fixture may be used to refit the V5 calibrator, select thresholds, tune a policy, or run
runtime control. The remaining final mixed-reliability family and adversarial families remain
quarantined. This stage is fixture authoring only.

## Next authorised artifact

`v5-final-evaluation-mixed-reliability-contrast-fixtures`
