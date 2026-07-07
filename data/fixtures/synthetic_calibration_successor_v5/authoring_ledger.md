# V5 Authoring Ledger

## Ledger status

```text
fixture_set_id=synthetic-calibration-successor-v5
registry_status=calibration_mixed_reliability_contrast_authored
runtime_input_assets=48
expected_outcome_assets=48
calibration_observations_authored=192
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
`CSV5-125..CSV5-136` remain self-authored synthetic calibration-only workload-variation pairs.
`CSV5-137..CSV5-148` are self-authored synthetic calibration-only mixed-reliability contrast
pairs. The new family balances `structured_text`, `code`, and `open_ended_chat` across four cases
each. It preserves both high-confidence/weak-acceptance and lower-confidence/stronger-acceptance
regions without exposing evaluation labels in runtime inputs.

Runtime inputs contain only decision-time scheduler context. Candidate token identifiers and
post-hoc labels remain in separate expected-outcome assets.

## Evidence boundary

This slice completes V5 calibration-case authoring. The 192 authored observations are not yet a
frozen fit corpus and may not be used for a V5 fit until one immutable calibration manifest is
authored and validated.

## Next authorised artifact

`v5-calibration-manifest-freeze`
