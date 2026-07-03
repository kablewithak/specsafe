# V3 Evidence Isolation and Promotion Gates

## Purpose

This document turns the V3 charter into practical repository rules. It protects the project from two failures:

1. changing the experiment after seeing a favourable or unfavourable final result; and
2. allowing a seemingly useful policy to use information it would not possess at decision time.

## Evidence namespaces

V3 assets must use an explicit V3-only root and V3-only identifiers. The final path names will be chosen in the V3 method-and-evidence constitution, but their meaning must remain separate from V1 and V2.

| Namespace | Allowed role | Forbidden role |
|---|---|---|
| V3 development | Loader/schema tests | Fit, tuning, final comparison |
| V3 calibration | Fit and finite model selection | Final outcome or policy tuning after lock |
| V3 final evaluation | One frozen final assessment and comparison | Fit, threshold selection, retry shaping |
| V3 adversarial regression | Known-risk regression protection | Final metric optimization |
| V1/V2 closed assets | Historical record and their own integrity tests | V3 design, fitting, thresholds, case design, score interpretation |

## Information boundary

Every valid V3 runtime policy must receive only lawful decision-time fields. It may use:

- request and workload metadata;
- current decode round and candidate position;
- lawfully visible earlier prefix state;
- pre-sample confidence for the current position;
- declared capacity snapshot;
- fixed policy configuration and calibration-fitness state.

It must not use:

- current or future candidate-token values where not lawfully visible;
- current or future verification outcomes;
- observed labels;
- final-evaluation results;
- retrospective best prefixes;
- future-derived features.

## Frozen-decision sequence

```text
method and evidence constitution
  -> fresh V3 calibration assets
  -> freeze fitter / finite selection procedure / policy configuration
  -> fresh V3 final-evaluation assets
  -> lock final-evaluation manifest
  -> run one held-out calibration assessment
  -> determine fitness or fallback
  -> run policy comparison under locked profiles
  -> retain the result without in-place retuning
```

A different sequence is invalid unless a new experiment version and fresh final-evaluation set are created.

## Promotion gates

### Gate 1 — Calibration fitness

A probability-driven adaptive policy may run only when the V3 held-out calibration assessment passes the predeclared gate.

If it fails:

```text
confidence_not_fit_for_automated_scheduling
  -> conservative fallback
  -> no probability-driven adaptive-policy advantage claim
```

### Gate 2 — Causal validity

Every policy-comparison report must retain a causal-safety status. A policy that exposes or consumes forbidden information is reported separately as an invalid negative control.

```text
causal failure
  -> utility result is invalid
  -> cannot support an adaptive-policy claim
```

### Gate 3 — Comparable inputs

A valid comparison requires the same:

- frozen trace manifest;
- capacity profile;
- scorer and utility formula;
- workload slice;
- evaluation protocol version.

### Gate 4 — Conditional result reporting

A claim of advantage must name:

- the policy version;
- the named baseline(s);
- the workload and capacity condition;
- the evidence class;
- the preserved counterexamples, ties, or losses.

## Minimum report contract

Each V3 final report must include:

1. objective and hypothesis;
2. evidence class;
3. trace, calibration, and capacity manifest references;
4. policy configuration and hash;
5. calibration result and fitness decision;
6. causal-safety result;
7. utility and verification-spend measures;
8. breakdown by workload and capacity condition;
9. negative and neutral cases;
10. failure labels;
11. residual risks and non-claims;
12. deterministic reproduction procedure.

## Hard stop conditions

Stop the current V3 line and retain the result if any of the following occurs:

- V3 final-evaluation data influences fitting or threshold choice;
- a runtime policy receives forbidden information;
- the frozen final manifest changes after lock;
- the confidence gate is unfit and a probability-driven policy is still run as valid;
- a claimed improvement disappears when inputs are made comparable;
- a proposed fix requires viewing or reusing V3 final outcomes.

## What this protects

These rules do not guarantee that V3 will show an adaptive-policy advantage. They guarantee that whatever V3 finds can be inspected, reproduced, and trusted within its stated evidence boundaries.
