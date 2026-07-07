# V5 Authoring Ledger

## Ledger status

```text
fixture_set_id=synthetic-calibration-successor-v5
registry_status=final_mixed_reliability_contrast_authored
calibration_runtime_input_assets=48
calibration_expected_outcome_assets=48
calibration_observations_frozen=192
calibration_manifest=frozen
calibration_artifact=retained
fit_diagnostics=retained
final_evaluation_runtime_input_assets=36
final_evaluation_expected_outcome_assets=36
final_evaluation_observations_authored=144
final_evaluation_manifest=absent
heldout_result=absent
```

## Evidence record

`CSV5-101..CSV5-148` remain frozen calibration-only case pairs. Their manifest, calibration
artifact, and diagnostics are unchanged. The four held-out families, `CSV5-201..CSV5-236`, are
self-authored synthetic curve-coverage, position-spread, workload-variation, and mixed-reliability
contrast evidence. They are stored under `final_evaluation/` so they cannot enter calibration asset
discovery or the calibration manifest.

The final mixed-reliability family contains deliberately inspectable high-confidence/weak-observed
acceptance and lower-confidence/stronger-observed-acceptance regions. This is held-out diagnostic
coverage, not a tuning instruction.

Runtime inputs contain decision-time scheduler context only. Candidate token identifiers,
acceptance labels, and prefix-survival labels remain physically separate in expected-outcome assets.
The final assets are not a final-evaluation manifest and do not establish a held-out calibration
result.

## Evidence boundary

No final fixture may be used to refit the V5 calibrator, select thresholds, tune a policy, or run
runtime control. Adversarial families remain quarantined. This stage completes final-fixture
authoring only.

## Next authorised artifact

`v5-final-evaluation-manifest-freeze`
