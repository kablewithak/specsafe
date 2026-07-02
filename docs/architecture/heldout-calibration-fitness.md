# Held-Out Calibration Fitness and Promotion Gate

## Purpose

This boundary applies a previously frozen calibration artifact to governed `final_evaluation`
evidence exactly once as an assessment artifact. It compares raw and calibrated probabilities
using Brier score, expected calibration error, and fixed equal-width diagnostic bins. It then
records a typed promotion decision.

The boundary is post-hoc. It never exposes labels to a runtime scheduler and it never refits,
retunes, mutates, or replaces the frozen calibrator.

## Required ordering

```text
calibration split
  -> fit frozen calibration artifact
  -> freeze artifact with provenance
  -> final_evaluation split
  -> assess raw versus calibrated probabilities
  -> retain promotion decision
  -> either close the candidate or start a wholly new redesign
```

Final-evaluation evidence may assess an already frozen artifact. It may not select bin counts,
alter temperature, relax fitness thresholds, choose policy thresholds, or re-fit the artifact.

## Inputs and boundaries

The held-out assessment accepts only:

- the exact `CalibrationRedesignFinalManifestedFixtureSet` contract;
- the exact `LogitTemperatureScalingArtifact` contract;
- the fixed `HeldOutTemperatureScalingAssessmentProtocol`.

The final manifest must contain only quarantined `final_evaluation` /
`held_out_evaluation` evidence. The artifact must prove calibration-only provenance and its
fitted case IDs must remain disjoint from the assessed final case IDs.

## Promotion gate

| Condition | Status | Promotion decision |
|---|---|---|
| Fewer held-out observations than the protocol minimum | `insufficient_held_out_data` | Not promoted |
| Calibrated Brier or expected calibration error is worse than raw | `calibrator_regression` | Not promoted |
| Neither metric is worse, but one or both strict improvement requirements are missed | `no_material_held_out_improvement` | Not promoted |
| Both metrics meet predeclared requirements | `passes_held_out_fitness` | Eligible only for later adaptive-policy research design |

A passing result would not authorize runtime control. Every result retains:

```text
runtime_control_eligibility=not_eligible_pending_adaptive_policy_evaluation
```

## Controlled result: Logit Temperature Scaling V1

The frozen `logit-temperature-scaling-v1` artifact was assessed against the immutable final
manifest with aggregate hash:

```text
be496cf719780e39b248b51d7d994ab8bafc3780d9abf5b094c86ba6d684831c
```

Assessment scope:

```text
assessed_case_ids=CRV1-009,CRV1-010,CRV1-011,CRV1-012
assessed_scenario_families=CRV1-FINAL-MIXED-RELIABILITY,CRV1-FINAL-ABRUPT-SUFFIX
observation_count=18
artifact_refit=false
artifact_mutated=false
```

| Metric | Raw | Calibrated | Improvement |
|---|---:|---:|---:|
| Brier score | 0.1420388888888889 | 0.14320093951851715 | -0.0011620506296282362 |
| Expected calibration error | 0.2483333333333333 | 0.20896181673124276 | 0.03937151660209054 |

The artifact improves expected calibration error but regresses Brier score. The predeclared
gate therefore rejects promotion:

```text
status=calibrator_regression
promotion_decision=not_promoted_calibrator_regression
adaptive_policy_research_eligibility=blocked_held_out_calibration_regression
runtime_control_eligibility=not_eligible_pending_adaptive_policy_evaluation
```

This is retained as a reproducible negative result. It blocks causal adaptive-policy work on
this artifact and fixture set. It must not trigger in-place tuning against the consumed final
evaluation corpus.

## Next valid path

The next valid technical path is either:

1. Stop at this negative result and package it as an audit-grade reliability proof; or
2. Start a separately governed `synthetic-calibration-redesign-v2` with new calibration and
   final-evaluation evidence, a candidate-method decision made before outcomes are authored,
   and a new read-only held-out promotion gate.

## Non-claims

This boundary does not fit or tune a calibrator, alter final-evaluation inputs, authorize a
runtime scheduler, define policy utility, compare scheduling policies, claim throughput benefit,
prove losslessness, or establish production readiness.
