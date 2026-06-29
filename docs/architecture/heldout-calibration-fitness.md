# Held-Out Calibration Fitness and Promotion Gate

## Purpose

This boundary applies a previously frozen calibration artifact to the governed
`final_evaluation` split exactly as an assessment artifact. It compares raw and calibrated
probabilities using Brier score, expected calibration error, and fixed equal-width diagnostic
bins. It then records a typed promotion decision.

The boundary is deliberately post-hoc. It does not expose labels to any runtime scheduler and
it never refits, retunes, mutates, or replaces the frozen calibrator.

## Required ordering

```text
calibration split
  -> fit FrozenCalibratorArtifact
  -> freeze artifact with provenance
  -> final_evaluation split
  -> evaluate raw versus calibrated probabilities
  -> retain promotion decision
```

The final-evaluation split may be used to assess the already frozen artifact. It may not be used
to select bin count, alter bin values, relax fitness thresholds, choose policy thresholds, or
re-fit the artifact.

## Inputs and exact-type boundaries

`evaluate_heldout_calibration_fitness(...)` accepts only:

- the exact `SyntheticTraceFixtureSet` contract;
- the exact `FrozenCalibratorArtifact` contract;
- an optional strict `HeldOutCalibrationFitnessProtocol`.

The artifact must match the assessed fixture-set ID and version exactly. The evaluator selects
only `TraceSplit.FINAL_EVALUATION` cases. Calibration, development, and adversarial-regression
outcomes are not read by this assessment function.

## Retained evidence

Every `HeldOutCalibrationFitnessResult` retains:

- the complete frozen calibrator artifact and its calibration-only provenance;
- assessed fixture-set ID and version;
- final-evaluation case and trace IDs;
- observation count;
- raw Brier score, ECE, and fixed-bin evidence;
- calibrated Brier score, ECE, and fixed-bin evidence;
- signed improvement values where positive means lower error after calibration;
- the assessment status, promotion decision, and adaptive-policy research eligibility;
- a permanent runtime-control ineligibility marker.

## Promotion gate

The gate is predeclared in `HeldOutCalibrationFitnessProtocol`.

| Condition | Status | Promotion decision |
|---|---|---|
| Fewer held-out observations than the protocol minimum | `insufficient_held_out_data` | Not promoted |
| Calibrated Brier or ECE is worse than raw | `calibrator_regression` | Not promoted |
| Calibration is not worse but does not clear both strict improvement requirements | `no_material_held_out_improvement` | Not promoted |
| Both metrics clear the predeclared strict improvement requirements | `passes_held_out_fitness` | Eligible for causal adaptive-policy research only |

A promotion permits the next **research-design** boundary. It does not authorize runtime policy
control. Every result retains:

```text
runtime_control_eligibility=not_eligible_pending_adaptive_policy_evaluation
```

## Current controlled result

On the present synthetic final-evaluation case, the frozen histogram calibrator regresses Brier
score and ECE relative to the raw confidence values. The expected decision is therefore:

```text
status=calibrator_regression
promotion_decision=not_promoted_calibrator_regression
adaptive_policy_research_eligibility=blocked_held_out_calibration_regression
```

This is retained as a negative result. It blocks causal load-aware policy work on the current
calibrator and fixture set rather than tuning against final evaluation.

## Non-claims

This boundary does not fit or tune a calibrator, alter final-evaluation inputs, authorize a
runtime scheduler, define policy utility, compare scheduling policies, claim throughput benefit,
prove losslessness, or establish production readiness.
