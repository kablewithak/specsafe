# Held-Out Calibration Fitness and Promotion Gate

## Purpose

This boundary records the read-only held-out fitness assessment for
`logit-temperature-scaling-v1` within `synthetic-calibration-redesign-v1`.

It is a historical evidence record. It does not authorize a V1 repair, V2 method choice,
fixture authoring, fitting, adaptive scheduling, or runtime control.

## Frozen evidence lineage

```text
candidate_artifact=logit-temperature-scaling-v1
artifact_version=1.0.0
artifact_fit_split=calibration
artifact_fit_case_ids=CRV1-001,CRV1-002,CRV1-003,CRV1-004,CRV1-005,CRV1-006
artifact_fit_manifest_aggregate_sha256=1de80a7e1556fff17e6032ab794177175ac250b2fa23598cdc8248f8aff00136

final_evaluation_case_ids=CRV1-009,CRV1-010,CRV1-011,CRV1-012
final_evaluation_manifest_aggregate_sha256=be496cf719780e39b248b51d7d994ab8bafc3780d9abf5b094c86ba6d684831c
held_out_observation_count=18
artifact_refit=false
artifact_mutated=false
```

## Predeclared protocol

```text
minimum_observation_count=16
equal_width_bin_count=10
minimum_brier_improvement=0.0
minimum_expected_calibration_error_improvement=0.0
```

Promotion required both Brier score and expected calibration error to improve or at least not
worsen according to the fixed gate. The gate was evaluated once after the artifact was frozen.

## Retained result

```text
raw_brier_score=0.1420388888888889
calibrated_brier_score=0.14320093951851715
brier_improvement=-0.0011620506296282362

raw_expected_calibration_error=0.2483333333333333
calibrated_expected_calibration_error=0.20896181673124276
expected_calibration_error_improvement=0.03937151660209054

status=calibrator_regression
promotion_decision=not_promoted_calibrator_regression
adaptive_policy_research_eligibility=blocked_held_out_calibration_regression
runtime_control_eligibility=not_eligible_pending_adaptive_policy_evaluation
```

Expected calibration error improved, but Brier score worsened. The artifact therefore failed
the predeclared gate and was not promoted.

## Consequences

- `logit-temperature-scaling-v1` is closed for promotion in this fixture set.
- V1 adaptive-policy research and runtime control remain blocked.
- The V1 final-evaluation corpus is consumed assessment evidence and cannot be used for
  successor method selection, fitting, threshold changes, fixture design, or re-evaluation.
- The artifact, fit report, manifests, and held-out report remain immutable audit evidence.
- Any successor is a new governed experiment, not an in-place V1 repair.

## Non-claims

This result does not prove that all calibration methods fail. It does not prove a scheduler
utility result, a throughput benefit, a cost reduction, losslessness, customer-data fitness,
Kaggle evidence, serving behavior, or production readiness.
