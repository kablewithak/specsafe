# ADR-0008: Retain V2 Bounded Platt Scaling as a Negative Result

- **Status:** Accepted
- **Date:** 2026-07-03
- **Decision scope:** `synthetic-calibration-redesign-v2`
- **Candidate artifact:** `bounded-platt-scaling-v1`
- **Supersedes:** No prior V2 closure decision.
- **Depends on:** ADR-0006, ADR-0007, the frozen V2 calibration manifest, the frozen V2 final-evaluation manifest, and the retained held-out assessment.

## Context

SpecSafe selected `bounded-platt-scaling-v1` before V2 runtime inputs or outcomes existed. The method was fixed as one global, bounded, monotonic logistic calibration transform with two fitted parameters. It was fitted only on the V2 calibration split and then frozen.

The V2 calibration corpus contains 12 calibration cases and 48 observations. The V2 final-evaluation corpus contains 9 quarantined cases and 36 observations across three families:

```text
CRV2-FINAL-DISTRIBUTION-SHIFT
CRV2-FINAL-LOCAL-DISAGREEMENT
CRV2-FINAL-ORDER-PERTURBATION
```

The final-evaluation manifest was frozen before assessment. The held-out assessment consumed the frozen artifact and the frozen final-evaluation manifest once.

## Decision

Retain `bounded-platt-scaling-v1` as a valid V2 negative result.

The held-out assessment result is:

```text
status=calibrator_regression
promotion_decision=not_promoted_calibrator_regression
adaptive_policy_research_eligibility=blocked_held_out_calibration_regression
runtime_control_eligibility=not_eligible_pending_adaptive_policy_evaluation
```

The artifact is not promoted. It must not control a scheduler, capacity policy, or runtime decision.

## Held-out evidence

```text
observation_count=36

raw_brier_score=0.28777777777777774
calibrated_brier_score=0.33919030111111326
brier_improvement=-0.051412523333335514

raw_expected_calibration_error=0.29222222222222227
calibrated_expected_calibration_error=0.3584753301794393
expected_calibration_error_improvement=-0.066253107957217

confidence_ordering_status=preserved
artifact_refit=false
artifact_mutated=false
assessment_attempt_count=1
```

The predeclared gate required strict improvement in both Brier score and expected calibration error. Both became worse. The result is therefore a regression even though the transform preserved confidence order.

## Consequences

### Permitted now

- Audit and reproduce the V2 fit, manifest, and held-out assessment.
- Explain the negative result in project documentation and portfolio material.
- Run a closure and design review for a possible future V3 experiment.
- Use the categorical fact that V2 was not promoted when deciding whether a fresh experiment is justified.

### Forbidden now

- Refit, retune, or alter `bounded-platt-scaling-v1` using V2 final-evaluation material.
- Change V2 thresholds, bins, promotion rules, fixture files, labels, case membership, capacity assumptions, or policy logic after the result.
- Run a second V2 final assessment as a fresh promotion attempt.
- Begin adaptive scheduling, capacity-utility claims, or runtime-control work from V2.
- Treat V2 calibration improvement on the calibration split as evidence of held-out success.

## V2 evidence quarantine

The following V2 material is consumed or audit-only. It must not be used as numerical, example-level, or test-expectation input for a V3 method choice, V3 fixture design, V3 fitting, V3 tuning, or V3 promotion rule:

```text
CRV2-101 through CRV2-112
CRV2-201 through CRV2-209
all V2 runtime and expected-outcome files
V2 calibration_manifest.json
V2 final_evaluation_manifest.json
bounded-platt-scaling-v1 artifact.json
bounded-platt-scaling-v1 fit_report.json
bounded-platt-scaling-v1 heldout_assessment.json
all V2 confidence values, labels, token IDs, trace IDs, hashes, metric values, and case patterns
```

V2 may be referenced only as a categorical, audit-only conclusion: the frozen global bounded-Platt candidate was not promoted on its held-out V2 assessment.

## What this does and does not mean

This decision proves that this specific frozen V2 candidate did not meet its own held-out gate on this controlled synthetic evidence.

It does not prove that all calibration methods fail, that confidence cannot be useful, or that no future scheduler can be safe or useful. Those claims would require a separately governed experiment with fresh evidence.

## Next safe boundary

Do not start V3 implementation automatically.

A V3 entry decision must first define a fresh question, a fresh candidate method or experiment design, fresh split rules, and fresh success criteria without using V2 data-bearing evidence. That decision must be recorded before V3 case bytes or outcomes exist.
