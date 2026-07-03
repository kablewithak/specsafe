# ADR-0009: Reopen SpecSafe for the Full North-Star Programme

- **Status:** Accepted
- **Date:** 2026-07-03
- **Decision owner:** Kabo Molefe
- **Applies from:** `main` after PR #40 (`d6fb772`)
- **Supersedes:** No previous ADR. It adds a governed V3 programme after V2 closure.

## Context

SpecSafe exists to answer one narrow question:

> Can an LLM verification scheduler spend limited verification compute more intelligently than blunt fixed rules while using only information available when each decision is made?

V1 and V2 established the project’s causal-safety, reproducibility, calibration, fixture-isolation, and held-out-assessment boundaries. V2’s frozen `bounded-platt-scaling-v1` artifact was assessed once against its locked V2 final-evaluation corpus and was **not promoted** because both declared probability-quality measures worsened. V2 is retained as a valid negative result.

The owner has decided to continue toward the full north star rather than stop at V2 portfolio packaging.

## Decision

SpecSafe will begin a **fresh V3 full north-star programme**.

The programme must build the missing proof layers required by the governing PRD:

1. fresh V3 evidence and a fresh, predeclared calibration protocol;
2. fixed-length and static-threshold baselines on identical evidence;
3. a causal, capacity-aware verification policy with a safe fallback;
4. controlled capacity profiles and comparison reports that preserve negative cases;
5. a separately labelled small-model empirical evidence layer, if the local core proof passes its gate;
6. public proof assets and final reconciliation.

V3 is not a repair attempt for V2. It is a new governed experiment with its own question, data, manifests, evidence gates, and final evaluation.

## Non-negotiable V3 isolation rule

The following V2 materials are **sealed from V3 method selection, fitting, threshold setting, fixture design, and final-score interpretation**:

- V2 final-evaluation runtime inputs and outcomes;
- V2 final-evaluation case IDs, labels, confidence values, and metrics;
- V2 calibration artifact parameters and fit report values;
- V2 final-assessment output values and failure breakdowns.

They may be retained only for historical documentation, repository integrity, and regression protection of V2’s own closed evidence boundary.

V3 may use the enduring project principles that existed before V2 evaluation: causal non-anticipation, split isolation, deterministic replay, evidence provenance, negative controls, and conservative fallback.

## V3 method-selection rule

Before V3 calibration data or final-evaluation data is authored, the repository must record exactly one of the following:

- a single fixed calibration method and fixed policy family; or
- a predeclared selection procedure that can choose from a finite set of methods using **V3 calibration data only**.

The record must also define the allowed decision-time features, fallback condition, fixed baselines, capacity-profile assumptions, success criteria, and failure criteria.

No V3 method, threshold, or capacity rule may be changed after V3 final-evaluation data is authored. A material change requires a new experiment version with fresh final-evaluation evidence.

## Programme gates

| Gate | Required outcome before proceeding |
|---|---|
| V3-A: charter | This ADR, the V3 charter, and isolation rules are merged. |
| V3-B: method and corpus constitution | A method-selection record and fresh V3 fixture constitution are merged before V3 case data exists. |
| V3-C: calibration readiness | V3 calibration corpus, manifest, fitter, metrics, and fallback gate are locally reproducible. |
| V3-D: final-evaluation lock | V3 final-evaluation corpus and manifest are frozen before the final evaluation runs. |
| V3-E: policy comparison | Baselines and the valid adaptive policy run on identical V3 traces and profiles; causal status is visible. |
| V3-F: empirical evidence | Small-model evidence is attempted only after the synthetic local comparison is complete. |
| V3-G: public release | Public assets are generated from retained evidence and reconciled with the final maturity statement. |

## Decision criteria

The full north star is not reached merely because a new calibrator improves a score.

The programme is complete only when the repository can show, under a fixed and reproducible protocol:

- which valid policy wins, ties, or loses against blunt baselines;
- the workload and capacity conditions associated with each outcome;
- whether the result is based on synthetic controlled evidence or small-model measured evidence;
- whether the policy used only lawful decision-time information;
- where the policy safely falls back rather than makes a probability-driven decision.

## Consequences

### Positive

- The project can move from calibration-only evidence to the original scheduler-comparison question.
- V2’s negative result remains credible and useful.
- Future claims will rest on a governed sequence rather than a post-hoc search for a winning chart.

### Costs and risks

- V3 requires fresh assets and cannot recycle V2 evidence for convenience.
- The programme may end with mixed or negative policy-comparison results.
- Full completion requires substantially more work than a portfolio-only closeout.

## Budget posture

Planning envelope from this decision point:

- **Core local proof:** approximately 70–95 additional hours.
- **Small-model empirical layer and public proof:** approximately 30–45 additional hours.
- **Total V3 programme envelope:** approximately 100–140 additional hours.

These are planning ranges, not evidence of time already worked.

## Status after merge

This ADR authorizes V3 planning only. It does **not** authorize V3 data authoring, calibration fitting, scheduler implementation, or a public claim that an adaptive policy improves anything.
