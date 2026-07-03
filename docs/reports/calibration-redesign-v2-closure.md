# Calibration Redesign V2 Closure Report

## Purpose

This report closes the V2 bounded-Platt calibration experiment.

The aim was simple: test whether one frozen confidence-adjustment rule could make confidence numbers more reliable on hidden cases without breaking the project’s fairness rules.

## Question tested

```text
Can the frozen global bounded-Platt calibration rule improve both
Brier score and expected calibration error on a locked V2 hidden-test set?
```

## What was prepared before the result

The experiment was set up in this order:

1. Pick one method before V2 fixture data existed.
2. Create separate calibration cases and hidden test cases.
3. Freeze a calibration-only manifest for 12 cases and 48 observations.
4. Fit the method only on calibration data.
5. Freeze the fitted artifact.
6. Create and freeze a separate hidden-test manifest for 9 cases and 36 observations.
7. Run one read-only hidden-test assessment.

This order matters because the hidden result could not change the method, its parameters, or the test set before the result was recorded.

## Frozen method

```text
artifact_id=bounded-platt-scaling-v1
method=one global confidence-adjustment rule
fit_cases=12
fit_observations=48
final_evaluation_accessed_before_assessment=false
```

The fitted rule was monotonic: it kept the same overall ranking from low confidence to high confidence.

## Hidden test set

```text
hidden_families=3
hidden_cases=9
hidden_observations=36
```

The hidden test set included:

- distribution-shift cases;
- local disagreement cases, where confidence order and outcomes do not always line up cleanly;
- order-perturbation cases, where the same confidence/outcome pairs appear in a different sequence.

## Result

| Measure | Raw confidence | Frozen rule | Change |
|---|---:|---:|---:|
| Brier score, lower is better | 0.2877777778 | 0.3391903011 | worse by 0.0514125233 |
| Calibration error, lower is better | 0.2922222222 | 0.3584753302 | worse by 0.0662531080 |
| Confidence ordering | preserved | preserved | no ranking reversal |

The gate required strict improvement in both main measures. The frozen rule made both worse.

```text
status=calibrator_regression
promotion_decision=not_promoted_calibrator_regression
adaptive_policy_research_eligibility=blocked_held_out_calibration_regression
```

## Interpretation

The main finding is narrow and useful:

> The single global bounded-Platt rule fitted on the V2 calibration cases did not generalize well enough to the locked V2 hidden cases.

The hidden cases exposed a mismatch between what the rule learned from the calibration data and what happened in the hidden data.

The result is consistent with a global two-parameter adjustment being too limited for these controlled conditions. That is a possible explanation, not a proven root cause. The experiment was not designed to isolate one reason for the failure.

## What we did not do after seeing the result

We did not:

- change the calibration rule;
- refit it using hidden outcomes;
- change the hidden cases;
- change the grading rules;
- run another attempt to try to get a better result;
- begin scheduler work anyway.

That restraint is part of the value of the project.

## What V2 now proves

V2 proves that SpecSafe can:

- keep learning data and hidden test data separate;
- freeze a method before hidden results exist;
- reproduce the fit and assessment from stored evidence;
- record a failed result instead of hiding it;
- block later system work when the confidence rule is not good enough.

## What V2 does not prove

V2 does not prove:

- that confidence is never useful;
- that all calibration methods fail;
- that an adaptive scheduler should be built;
- that the project saves money, reduces delay, or improves real-world AI systems;
- that SpecSafe is production-ready.

## Status after closure

```text
V2 calibration experiment=closed
V2 result=valid negative result
V2 artifact=not promoted
V2 scheduler research=blocked
V2 runtime control=not eligible
```

## Recommended next step

Pause implementation and decide whether a fully fresh V3 experiment is worth the time.

A V3 experiment is justified only if it asks a meaningfully new question, chooses its method before V3 data exists, and uses fresh calibration and hidden-test evidence. V2 values, labels, cases, and metrics must not be used to shape that new experiment.
