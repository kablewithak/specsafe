# V5 Authoring Ledger

## Ledger status

```text
fixture_set_id=synthetic-calibration-successor-v5
registry_status=calibration_curve_coverage_authored
runtime_input_assets=12
expected_outcome_assets=12
calibration_observations_authored=48
calibration_manifest=absent
calibration_artifact=absent
fit_diagnostics=absent
final_evaluation_assets=0
final_evaluation_manifest=absent
heldout_result=absent
```

## Authoring record

`CSV5-101..CSV5-112` are self-authored synthetic calibration-only curve-coverage case pairs.
They provide four workloads each for `structured_text`, `code`, and `open_ended_chat`, with four
candidate positions per case. Runtime inputs contain only decision-time scheduler context; labels
and candidate token identifiers remain in the separate expected-outcome assets.

## Evidence boundary

This slice does not create a calibration manifest. The 48 authored observations are not yet a
frozen fit corpus and may not be used for a V5 fit until the complete 48-case calibration corpus
is authored and its manifest is frozen.

## Next authorised artifact

`v5-calibration-position-spread-fixtures`
