# Calibration Split and Raw-Confidence Fitness

## Purpose

This boundary creates an immutable synthetic `calibration` split and evaluates raw
confidence as a diagnostic input. It exists before a calibrator and before an adaptive
scheduler so those later additions cannot tune against final-evaluation cases.

## Fixture posture

`STF-005` and `STF-006` are self-authored, token-ID-only calibration fixtures. Their
runtime input and expected outcome assets remain structurally separated and hash-verified
by the existing fixture manifest. They are not policy-tuning or final-evaluation assets.

The manifest now records six cases across four governed splits:

- development: 2 cases;
- calibration: 2 cases;
- adversarial regression: 1 case;
- final evaluation: 1 case.

## Diagnostic protocol

`evaluate_raw_confidence_fitness(...)` accepts only the exact
`SyntheticTraceFixtureSet` contract. It selects `TraceSplit.CALIBRATION` cases only, then
joins each context's `conditional_survival_confidence` with the corresponding
post-hoc `observed_acceptance` label after fixture loading and alignment validation.

The predeclared protocol retains:

- minimum observation count;
- fixed equal-width bin count;
- maximum Brier score;
- maximum expected calibration error.

The result retains raw-confidence summary statistics and every bin summary. It does not
fit a calibrator, alter a policy configuration, choose a confidence threshold, compute a
policy utility, or assign a winner.

## Status meanings

- `insufficient_calibration_data`: too few calibration observations for the protocol.
- `fails_precalibration_screen`: the raw score misses one or more predeclared diagnostic
  thresholds.
- `passes_precalibration_screen`: the raw score meets diagnostic thresholds. This is still
  not evidence of calibration quality or runtime eligibility.

Every result remains permanently labelled:

```text
automation_control_eligibility=not_eligible_pending_held_out_calibration
```

This means a passing raw-confidence diagnostic cannot authorize automated scheduling, an
adaptive policy, a production threshold, or a performance claim. A later slice must add a
calibrator, preserve split boundaries, and evaluate its fitness on held-out evidence.

## Current non-claims

This implementation does not claim calibrated confidence, adaptive-policy value, capacity
efficiency, a baseline winner, final-evaluation performance, Kaggle evidence, throughput,
losslessness, or production readiness.
