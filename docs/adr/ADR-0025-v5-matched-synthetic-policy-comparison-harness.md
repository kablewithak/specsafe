# ADR-0025: Add a Case-Level Matched Synthetic Policy Comparison Harness

- **Status:** Accepted
- **Date:** 2026-07-07
- **Decision owner:** SpecSafe project owner
- **Scope:** Local synthetic replay only

## Context

SpecSafe now has the prerequisites for a governed causal-policy comparison:

- strict causal scheduler contexts and an isolated unsafe retrospective control;
- valid fixed-length and static-threshold baselines with hashable provenance;
- a retained V5 calibration artifact eligible for controlled policy research only;
- a calibrated causal load-aware policy that depends on one declared synthetic capacity profile;
- versioned synthetic capacity profiles;
- a shared synthetic policy-utility scorer.

Those pieces alone do not make a valid comparison. A comparison is valid only when every valid policy runs on the same immutable replay case, with the same declared capacity profile and the same declared utility formula. The unsafe retrospective control must remain visible, but it must be structurally excluded from valid scoring and from any adaptive-versus-baseline utility delta.

The current scoring boundary permits development and adversarial-regression cases only. Final-evaluation comparison remains unauthorized until a separate governed final comparison protocol exists. No policy is promoted by a case-level result.

## Decision

Add a case-level matched synthetic policy comparison harness in `specsafe.eval_harness`.

The harness shall accept exactly:

1. one `SyntheticTraceFixtureSet`;
2. one development or adversarial-regression case from that set;
3. one exact `SyntheticCapacityProfile` whose identity matches every runtime snapshot in the selected case;
4. one fixed-length baseline;
5. one static-threshold baseline;
6. one retained-artifact-backed calibrated causal load-aware policy;
7. one evaluation-only unsafe retrospective look-ahead control;
8. one shared `PolicyUtilityScoringConfig`;
9. one immutable `MatchedPolicyComparisonConfig`.

The harness shall:

- run all three valid policies through the existing causal valid-replay path;
- score each valid replay through the existing shared scorer;
- run the unsafe control separately through the existing unsafe replay path;
- retain valid replays, scores, case-level deltas, and the unsafe-control exclusion in one strict result object;
- classify the adaptive policy as higher utility, neutral, or lower utility against each baseline for that one controlled case;
- retain no aggregate winner, promotion, runtime-control, throughput, latency, cost-saving, or production field.

## Formula alignment requirement

The adaptive policy’s `accepted_admission_value_units` and `marginal_verification_cost_weight` must exactly match the shared scoring configuration before comparison execution.

This prevents a subtle invalid comparison where the adaptive policy chooses actions under one objective but is scored under another.

## Unsafe-control rule

The unsafe retrospective control may run on the same immutable case to demonstrate apparent look-ahead behavior. It must retain:

```text
causal_safety_status=fail
evaluation_only=true
exclusion_reason=causal_safety_failure_excluded_from_valid_comparison
```

It must not receive a valid policy-utility score and must not appear in adaptive-versus-baseline deltas.

## Options considered

### Option A: Build a report first

Rejected. A report without a strict comparison result would risk mixing inputs, profiles, or scoring configurations and would not provide a dependable machine-readable evidence boundary.

### Option B: Compare policies through ad hoc test assertions

Rejected. Test assertions can prove individual examples, but they do not retain a reusable comparison artifact with replay, score, policy, profile, scorer, and invalid-control provenance together.

### Option C: Add a case-level comparison harness first

Accepted. This is the smallest maintainable step that makes matched comparison mechanics inspectable before authoring a governed multi-case comparison fixture programme or any final report.

## Consequences

### Easier now

- deterministic same-input policy comparison;
- retention of neutral, losing, and higher-utility controlled cases;
- strict unsafe-control separation;
- machine-readable comparison provenance;
- prevention of policy/scorer formula drift.

### Still prohibited

- final-evaluation comparison;
- cross-case winner selection;
- policy promotion;
- calibration refit or threshold tuning;
- profile tuning from outcomes;
- serving, throughput, latency, cost, or production claims;
- Kaggle and public replay release work.

## Evidence boundary

This harness produces **case-level synthetic controlled comparison evidence** only. A single higher-utility case is not a universal policy claim. Future work must author a governed multi-case comparison corpus, retain neutral and losing results, and produce a report with explicit validity markers before the project claims a bounded adaptive-policy advantage.
