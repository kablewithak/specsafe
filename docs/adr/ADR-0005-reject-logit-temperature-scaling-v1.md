# ADR-0005: Reject Logit Temperature Scaling V1 After Held-Out Regression

- **Status:** Accepted
- **Date:** 2026-07-02
- **Decision scope:** `synthetic-calibration-redesign-v1`
- **Candidate artifact:** `logit-temperature-scaling-v1`
- **Decision:** Rejected for promotion; adaptive-policy research remains blocked.

## Context

`logit-temperature-scaling-v1` was predeclared and fitted only on the frozen synthetic
`calibration` split. The fitted artifact retained calibration-only provenance:

```text
artifact_id=logit-temperature-scaling-v1
artifact_version=1.0.0
fit_split=calibration
fit_data_role=calibration
fitted_case_ids=CRV1-001,CRV1-002,CRV1-003,CRV1-004,CRV1-005,CRV1-006
sample_count=24
final_evaluation_accessed=false
runtime_control_eligible=false
```

The artifact was then assessed once against the independent, hash-verified
`final_evaluation` manifest containing `CRV1-009` through `CRV1-012`. The assessment was
read-only: it did not refit the artifact, alter its temperature, mutate fixture assets,
select thresholds, or configure a policy.

## Evidence reviewed

```text
final_evaluation_manifest_aggregate_sha256=be496cf719780e39b248b51d7d994ab8bafc3780d9abf5b094c86ba6d684831c
artifact_fit_manifest_aggregate_sha256=1de80a7e1556fff17e6032ab794177175ac250b2fa23598cdc8248f8aff00136
held_out_observation_count=18
minimum_observation_count=16

raw_brier_score=0.1420388888888889
calibrated_brier_score=0.14320093951851715
brier_improvement=-0.0011620506296282362

raw_expected_calibration_error=0.2483333333333333
calibrated_expected_calibration_error=0.20896181673124276
expected_calibration_error_improvement=0.03937151660209054
```

The fixed promotion protocol requires both Brier and expected calibration error not to worsen.
Expected calibration error improved, but Brier score regressed. The gate therefore returned:

```text
status=calibrator_regression
promotion_decision=not_promoted_calibrator_regression
adaptive_policy_research_eligibility=blocked_held_out_calibration_regression
runtime_control_eligibility=not_eligible_pending_adaptive_policy_evaluation
artifact_refit=false
artifact_mutated=false
```

## Decision

1. `logit-temperature-scaling-v1` is **rejected for promotion** in
   `synthetic-calibration-redesign-v1`.
2. No adaptive scheduling, verification policy, threshold selection, capacity profile,
   utility scorer, or runtime-control work may be justified by this artifact.
3. The final-evaluation corpus `CRV1-009` through `CRV1-012` is now **consumed
   assessment evidence** for this candidate artifact. It remains retained for audit but must
   not be used to tune, select, rebalance, or redesign a successor.
4. The artifact, its fit report, final manifest, and held-out assessment report remain
   immutable evidence. They may be inspected and reproduced, but not overwritten to revise
   the promotion decision.
5. The current project state is a valid negative result, not an incomplete positive result.

## Consequences

### Permitted claims

- A synthetic, split-isolated calibration experiment was fitted, manifest-verified, and
  assessed on independently authored final-evaluation evidence.
- The frozen logit-temperature artifact improved one reported metric but regressed another
  predeclared metric, so the promotion gate rejected it.
- The harness prevented an invalid transition from partial metric improvement to adaptive
  policy research or runtime control.

### Forbidden claims

- Temperature scaling improved calibration overall.
- Confidence is fit for automated verification scheduling.
- An adaptive policy is authorized.
- A policy utility winner exists.
- Any throughput, cost, latency, losslessness, customer-data, Kaggle, deployment, or
  production claim.

## Re-entry criteria for a future redesign

A future calibration redesign must be a new governed experiment, not an in-place repair.

```text
required_fixture_set_id=synthetic-calibration-redesign-v2
required_new_calibration_cases=yes
required_new_final_evaluation_cases=yes
required_new_scenario_family_fingerprints=yes
required_candidate_method_decision=before fixture outcomes are authored
required_calibration_manifest=separate and immutable
required_final_manifest=separate and immutable
required_held_out_assessment=single read-only promotion gate
```

The v1 held-out outcomes may be cited only as historical negative evidence. They must not
determine the v2 method, temperature, thresholds, bin count, fixture design, case balancing,
policy configuration, or acceptance criteria.

## Commercial proof angle

This is an AI Reliability Audit proof asset: the system preserved a clean evidence boundary and
blocked a false-positive promotion when a superficially favourable metric could have been used
to justify unsafe follow-on work.
