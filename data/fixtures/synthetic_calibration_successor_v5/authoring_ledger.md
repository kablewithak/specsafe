# V5 Authoring Ledger

## Ledger status

```text
fixture_set_id=synthetic-calibration-successor-v5
registry_status=final_evaluation_manifest_frozen
calibration_runtime_input_assets=48
calibration_expected_outcome_assets=48
calibration_observations_frozen=192
calibration_manifest=frozen
calibration_artifact=retained
fit_diagnostics=retained
final_evaluation_runtime_input_assets=36
final_evaluation_expected_outcome_assets=36
final_evaluation_observations_frozen=144
final_evaluation_manifest=frozen
final_evidence_index=frozen
heldout_result=absent
```

## Evidence record

`CSV5-101..CSV5-148` remain frozen calibration-only case pairs. Their calibration manifest,
calibration artifact, and fit diagnostics are unchanged. `CSV5-201..CSV5-236` are independently
frozen held-out case pairs spanning curve coverage, position spread, workload variation, and
mixed-reliability contrast.

`final_evaluation_manifest.json` hash-addresses all 72 held-out assets and records the aggregate
integrity hash. `final_evidence_index.json` is a label-free inventory of case IDs, trace IDs,
workloads, families, and paired paths. Both reference the final pre-freeze registry state.

Runtime inputs retain only decision-time scheduler context. Candidate token identifiers,
acceptance labels, and prefix-survival labels remain physically separate in expected-outcome assets.
The final manifest does not fit or refit the calibrator and does not create a held-out result.

## Evidence boundary

No final fixture may be used to refit the V5 calibrator, select thresholds, tune a policy, or run
runtime control. Adversarial families remain unauthored and quarantined. The next step is exactly
one governed held-out calibration assessment against frozen inputs.

## Next authorised artifact

`v5-final-heldout-calibration-assessment`
