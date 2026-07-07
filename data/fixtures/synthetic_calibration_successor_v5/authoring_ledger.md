# V5 Authoring Ledger

## Ledger status

```text
fixture_set_id=synthetic-calibration-successor-v5
registry_status=calibration_workload_variation_authored
runtime_input_assets=36
expected_outcome_assets=36
calibration_observations_authored=144
calibration_manifest=absent
calibration_artifact=absent
fit_diagnostics=absent
final_evaluation_assets=0
final_evaluation_manifest=absent
heldout_result=absent
```

## Authoring record

`CSV5-101..CSV5-112` remain self-authored synthetic calibration-only curve-coverage pairs.
`CSV5-113..CSV5-124` remain self-authored synthetic calibration-only position-spread pairs.
`CSV5-125..CSV5-136` are self-authored synthetic calibration-only workload-variation pairs.
The new family balances `structured_text`, `code`, and `open_ended_chat` across four cases each,
with four candidate positions per case. It retains overlapping confidence ranges across workloads
and preserves both accepted and rejected outcomes in every workload class.

Runtime inputs contain only decision-time scheduler context. Candidate token identifiers and
post-hoc labels remain in separate expected-outcome assets.

## Evidence boundary

This slice does not create a calibration manifest. The 144 authored observations are not yet a
frozen fit corpus and may not be used for a V5 fit until all 48 calibration cases are authored and
one calibration manifest is frozen.

## Next authorised artifact

`v5-calibration-mixed-reliability-contrast-fixtures`
