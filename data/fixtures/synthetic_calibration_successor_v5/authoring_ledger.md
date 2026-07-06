# V5 Authoring Ledger

## Ledger status

```text
fixture_set_id=synthetic-calibration-successor-v5
registry_status=schema_only
runtime_input_assets=0
expected_outcome_assets=0
calibration_manifest=absent
calibration_artifact=absent
fit_diagnostics=absent
final_evaluation_assets=0
final_evaluation_manifest=absent
heldout_result=absent
```

## Reservation decision

The V5 namespace is reserved before case authoring. The registry fixes separate calibration,
final-evaluation, and adversarial-regression ranges so later assets cannot be silently repurposed.

## Source constraints

All later V5 case content must be self-authored, public-safe, and independently designed.
This schema-only root contains no case-level runtime inputs, labels, outcomes, fitted parameters,
or final metrics.

## Next authorised artifact

`v5-calibration-curve-coverage-fixtures`

No other V5 artifact is authorised from this stage.
