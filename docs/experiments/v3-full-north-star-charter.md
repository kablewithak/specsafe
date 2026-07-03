# SpecSafe V3 Full North-Star Programme Charter

## Status

**Planning charter.**

This document authorizes a new V3 programme after V2 was closed as a valid negative calibration result. It does not make a V3 performance claim and does not reopen V2.

## Plain-English goal

Build a fair laboratory that can answer this question:

> When an AI is deciding whether to spend extra effort checking its work, can it make better choices than a simple fixed rule without using information from the future?

A good final result may show that the smarter rule helps in some conditions, ties in others, and safely refuses to act when its confidence cannot be trusted.

## Research question

> Under fixed V3 trace-replay conditions, can a causal, confidence-aware, capacity-aware verification policy achieve better declared policy utility than fixed-length and static-threshold baselines while preserving causal validity and a conservative fallback?

## What V3 must prove

V3 must produce retained evidence for all of the following:

1. **Fairness:** the runtime policy sees only information available at the time of its decision.
2. **Confidence quality:** the confidence signal is evaluated on V3 held-out data and either passes the declared fitness gate or triggers fallback.
3. **Comparable testing:** every valid policy runs on the same locked traces and the same named capacity profile.
4. **Useful comparison:** reports show where the adaptive policy wins, ties, or loses against fixed and static-threshold baselines.
5. **Safe limits:** reports distinguish synthetic controlled evidence from any small-model measured evidence and avoid production-serving claims.

## What V3 is not

V3 is not:

- a V2 retry;
- a search for a calibration curve that looks good after seeing final results;
- a production model-serving engine;
- a claim of real-world throughput or cost savings without separate deployment evidence;
- a dashboard-first project.

## Evidence separation

| Evidence area | May influence | Must not influence |
|---|---|---|
| V3 development fixtures | Schema and loader debugging only | Calibration selection, policy threshold, final claims |
| V3 calibration split | Predeclared calibration fit and finite method-selection procedure | Final report outcome, post-final threshold changes |
| V3 final-evaluation split | One final assessment and comparison report | Any fitting, choosing, retuning, or retrying |
| V3 adversarial regression split | Regression tests for known named failure modes | Final-threshold tuning |
| V1 and V2 closed evidence | Historical records and integrity checks only | Any V3 method, threshold, fixture, or result decision |

## V3 programme workstreams

### Workstream A — Method and evidence constitution

Before V3 data exists, define:

- the exact V3 method or a finite selection procedure;
- the allowed runtime features;
- the fixed baselines;
- the utility formula and its limits;
- the fallback rule;
- success, neutral, and failure outcomes;
- fresh V3 case-family requirements;
- prohibited V2 influence.

**Exit gate:** a reviewable record exists before V3 evidence authoring begins.

### Workstream B — Fresh controlled evidence

Create fresh, self-authored V3 case families for:

- light, moderate, saturated, and jagged capacity conditions;
- easy versus difficult candidate positions;
- high-confidence long-prefix cases;
- low-confidence early-stop cases;
- fixed-rule-wins cases;
- static-threshold-wins cases;
- confidence-unfit fallback cases;
- causal-look-ahead negative controls;
- request competition and uneven marginal value.

The V3 final-evaluation cases must be different from all V1 and V2 final-evaluation cases at the task/case level.

**Exit gate:** manifests, provenance, hashes, and split checks are deterministic.

### Workstream C — Calibration and fallback

Build the selected V3 calibration boundary using V3 calibration data only. Retain:

- raw and calibrated Brier score;
- expected calibration error;
- discrimination measure;
- per-position and prefix-level measurements;
- fixed fitness gate;
- deterministic conservative fallback when the gate fails.

**Exit gate:** fit and held-out calibration assessment are reproducible, with no V3 policy comparison claim yet.

### Workstream D — Policy and capacity comparison

Implement and compare, under identical locked inputs:

1. fixed-length baseline;
2. static confidence-threshold baseline;
3. causal, confidence-aware, capacity-aware policy;
4. unsafe retrospective negative control, reported as invalid.

The report must include decision mix, admitted verification positions, low-value verification, declared utility, causal status, and breakdown by workload and capacity regime.

**Exit gate:** a valid policy-comparison report preserves wins, ties, losses, and fallback cases.

### Workstream E — Small-model evidence

Only after the local proof is complete, collect a small-model trace set in a documented Kaggle environment using a compatible model pair and sanitized exports.

**Exit gate:** environment-specific evidence is explicitly labelled and does not replace the local deterministic harness.

### Workstream F — Public proof and reconciliation

Package retained evidence into the repository, case study, replay demo, and final maturity statement.

**Exit gate:** every public claim has a retained artifact, reproduction path, and explicit evidence class.

## Predeclared success language

V3 may use one of these outcomes only after the locked final comparison:

| Outcome | Meaning |
|---|---|
| `VALID_ADAPTIVE_ADVANTAGE` | The valid adaptive policy improves the declared utility over the named baseline(s) under stated V3 conditions and passes all gates. |
| `VALID_CONDITIONAL_ADVANTAGE` | The adaptive policy helps only in named workload/capacity conditions; losses and limits remain visible. |
| `VALID_NEUTRAL_OR_MIXED_RESULT` | No consistent advantage is demonstrated, but the comparison is valid and useful. |
| `CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY` | The confidence gate failed and conservative fallback prevented a probability-driven claim. |
| `INVALID_CAUSAL_COMPARISON` | A policy used forbidden information; its utility result is invalid. |

No final result may be described as a production speedup, live-traffic result, or universal policy advantage.

## Time budget

| Workstream | Planning range |
|---|---:|
| A — Method and evidence constitution | 6–10 hours |
| B — Fresh controlled evidence | 16–24 hours |
| C — Calibration and fallback | 18–25 hours |
| D — Policy and capacity comparison | 28–40 hours |
| E — Small-model evidence | 15–25 hours |
| F — Public proof and reconciliation | 18–26 hours |
| **Total additional effort** | **101–150 hours** |

The ranges are planning estimates. Actual progress will be recorded only after merged, validated work.

## First authorised next action

Create the V3 method-and-evidence constitution. It must happen before any V3 case files, manifests, fit code, or scheduler code are authored.
