# ADR-0016: Close V4 After the Held-Out Ranking-Safety Regression

- **Status:** Accepted
- **Date:** 2026-07-07
- **Decision owner:** Kabo Molefe
- **Applies from:** `main` after PR #70 is merged
- **Depends on:** ADR-0014, ADR-0015, PR #66, PR #67, PR #68, PR #69, PR #70
- **Supersedes:** Nothing. This decision closes the V4 programme; it does not alter V1, V2, or V3 evidence.

## Context

ADR-0015 defined V4 as a fresh, fixed-method calibration programme. It required one immutable
calibration corpus, one immutable final-evaluation corpus, a frozen regularized-isotonic artifact,
and one complete held-out calibration gate before any scheduler, policy comparison, baseline,
capacity-policy, replay, or runtime-control work could begin.

PR #70 executed that one permitted assessment against the frozen V4 final corpus:

```text
36 held-out cases
144 held-out observations
4 candidate positions per case
```

The completed result is retained at:

```text
evidence/heldout-calibration/v4-final-heldout-calibration-assessment-v1/result.json
```

Its SHA-256 is:

```text
83ed589bc46499c90c8fff78a4b6c475a889e7eb02e7372ec5fad0af27f8c3d6
```

The assessment verified provenance, complete case coverage, complete per-position coverage,
write-once persistence, no calibration refit, and no scheduler or policy execution. It then
retained these aggregate metrics:

| Metric | Raw | Calibrated | Delta | Gate |
|---|---:|---:|---:|---|
| Brier score | 0.133103062500 | 0.097672325103 | +0.035430737397 | Pass: improvement >= 0.010000 |
| ECE, 10 bins | 0.231326388889 | 0.192901234568 | +0.038425154321 | Pass: improvement >= 0.020000 |
| AUROC | 0.983984375000 | 0.971093750000 | -0.012890625000 | Fail: degradation must be no worse than -0.002000 |

The retained result status is:

```text
RANKING_SAFETY_REGRESSION
```

The assessment therefore correctly reports:

```text
adaptive_policy_research_eligibility=blocked
runtime_control_eligible=false
fallback_policy_id=fixed_short_1
```

## Decision

V4 is closed as a valid, complete, immutable held-out calibration result with a
`RANKING_SAFETY_REGRESSION`.

This is not classified as an implementation failure. The result is valid because:

- the frozen calibration and final-evaluation provenance checks passed;
- all 36 held-out cases and all 144 held-out observations were assessed;
- no final-evaluation refit, threshold tuning, scheduler execution, or policy execution occurred;
- the result is canonical, hash-anchored, and write-once;
- Brier and ECE improvements exceeded their predeclared floors; and
- the independently predeclared ranking-safety gate failed.

V4 is therefore an accepted negative result. It must be retained, not repaired in place.

## Required consequences

### 1. V4 final evidence is consumed

The V4 final-evaluation corpus, final manifest, final-evidence index, assessment result, and
assessment status are immutable historical evidence.

They must not be used to:

- tune, refit, smooth, replace, or select a V4 calibration mapping;
- adjust a V4 threshold, capacity cost, replay score, baseline rule, or policy configuration;
- author a new V4 final case;
- rerun or overwrite the V4 final assessment;
- select a policy or claim a policy advantage.

### 2. V4 policy work remains blocked

No V4 scheduler, baseline comparison, replay scorer, capacity policy, adaptive policy, runtime
integration, deployment, or production-readiness claim is authorized.

The retained `fixed_short_1` fallback is a conservative boundary, not a V4 policy recommendation
or a production-control authorization.

### 3. The failure is specifically ranking safety

The decision does not claim a single unproven mathematical cause for the AUROC reduction.

The proven fact is narrower: the frozen V4 calibrated probabilities improved Brier score and ECE
while reducing AUROC by `0.012890625000`, beyond the allowed degradation of `0.002000`.

Any future programme must preserve the distinction between:

- probability calibration quality; and
- ranking preservation.

A future gate must continue to retain both dimensions explicitly.

### 4. V4 remediation is a fresh-programme decision, not a V4 patch

A future successor programme may be proposed only through a new method-and-evidence constitution.

That proposal must:

- use a new fixture root and a new case namespace;
- predeclare the calibration method and all gate criteria before new fixture authoring;
- retain a ranking-safety gate before any policy comparison;
- keep runtime inputs and post-hoc outcomes physically separate;
- use a fresh calibration split and a fresh final-evaluation split;
- prohibit final-evaluation refit, threshold selection, and result overwrite; and
- make no selection of successor-method parameters from V4 held-out labels or V4 final outcomes.

V4 can contribute process lessons: preserve rank safety as a first-class gate, keep evidence
write-once, and fail closed before policy work. V4 final case bytes, outcome labels, and held-out
results are not successor-programme tuning inputs.

## Alternatives considered

| Alternative | Decision | Reason |
|---|---|---|
| Promote V4 because Brier and ECE improved | Rejected | A complete pass required ranking safety as well. |
| Tune or refit the V4 mapping after the final result | Rejected | This would contaminate consumed held-out evidence. |
| Continue to V4 policy and baseline comparisons | Rejected | ADR-0015 blocks policy work after a non-passing gate. |
| Run V4 adversarial assets as a substitute for remediation | Rejected | Adversarial evidence cannot repair a failed held-out calibration gate or authorize policy work. |
| Retain the failure, close V4, and define a fresh successor programme later | Accepted | This preserves evidence integrity and keeps the next experiment inspectable. |

## Operational closeout

This ADR authorizes no further V4 implementation artifact.

The next immediate activity is a formal V4 closeout handover after an architecture Q&A review.
A future fresh-programme charter may be considered only after that handover is complete.

## Consequences

### Positive

- The project retains a trustworthy negative result instead of hiding it behind retuning.
- The V4 final-evaluation corpus remains credible historical evidence.
- The policy layer is prevented from inheriting a ranking-unsafe calibration map.
- The next programme starts from a clean evidence boundary.

### Costs

- V4 does not progress to policy comparison or runtime-control work.
- A successor programme must create fresh evidence rather than recycling V4 final outcomes.
- The project must spend effort on a new method constitution before another implementation cycle.

## Acceptance criteria

This decision is complete only when:

- this ADR is merged;
- the V4 proposal manifest and authoring ledger identify the completed negative result;
- no V4 evidence bytes, artifact bytes, result bytes, or runtime source files are changed;
- the working tree returns to clean `main`; and
- the next formal artifact is the V4 closeout handover, not a policy implementation.
