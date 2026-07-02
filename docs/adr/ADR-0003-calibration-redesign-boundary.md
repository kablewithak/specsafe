# ADR-0003: Quarantine the Consumed Held-Out Calibration Fixture and Govern Calibration Redesign

- **Status:** Proposed — pending review and merge
- **Date:** 2026-07-02
- **Decision owner:** SpecSafe project owner
- **Related PRD sections:** 4.1, 6, 10, 11.5, 15, 17, 21, 25, 29
- **Related architecture note:** `docs/architecture/calibration-redesign-protocol.md`
- **Supersedes:** None
- **Does not supersede:** The current held-out calibration assessment or its negative result

## Context

SpecSafe completed Phase 3 calibration and confidence fitness with a frozen equal-width
histogram calibrator. The artifact was fitted only from the governed `calibration` split
using `STF-005` and `STF-006`, then assessed once against the governed
`final_evaluation` split using `STF-004`.

The held-out assessment retained a negative result:

```text
calibrator_status=calibrator_regression
promotion_decision=not_promoted_calibrator_regression
adaptive_policy_research_eligibility=blocked_held_out_calibration_regression
runtime_control_eligibility=not_eligible
```

The result is valid evidence. It proves that this frozen histogram artifact did not earn
promotion under the predeclared held-out fitness gate. It does not prove that every
possible calibration method is unfit, that confidence can never be calibrated, or that
an adaptive scheduling policy can be implemented anyway.

The project must not use the observed result to optimize the existing artifact. In
particular, changing histogram bin count, bin boundaries, fallback behavior, fit
thresholds, promotion thresholds, or policy logic after reviewing `STF-004` would turn
the final-evaluation fixture into a tuning asset and invalidate its role as held-out
evidence.

The next decision is therefore not “try another calibrator until it wins.” The next
decision is to freeze a new, inspectable protocol that governs any redesigned method,
its fresh evidence, its promotion gate, and its failure response before any new fit or
assessment is performed.

## Decision

SpecSafe adopts the following calibration-redesign boundary.

### 1. `STF-004` is permanently quarantined from redesign work

`STF-004` remains retained evidence of the completed histogram-calibrator assessment.
It may be read only to establish these categorical facts:

- the prior artifact was assessed;
- it regressed under the prior protocol;
- it was not promoted;
- adaptive policy work is blocked for that artifact and fixture combination.

`STF-004` must not be used to select, tune, rank, reject, or modify any future:

- calibration method;
- calibration parameterization;
- binning scheme;
- fallback rule;
- fitness threshold;
- capacity rule;
- policy threshold;
- fixture scenario;
- report framing.

No new implementation test may encode its observed metric values as an optimization
target. Existing regression tests that protect the prior assessment boundary remain
permitted.

### 2. The next candidate method is predeclared as global logit temperature scaling

The next candidate artifact is:

```text
artifact_id=logit-temperature-scaling-v1
method=single-positive-temperature-on-logit-confidence
scope=global-only
fit_target=conditional_survival_confidence
```

The artifact applies one positive scalar temperature to valid open-interval confidence
values. It is deliberately constrained:

- one global parameter only;
- no workload-specific temperature;
- no position-specific temperature;
- no adaptive binning;
- no outcome-dependent fallback choice;
- no policy behavior attached to the artifact;
- no final-evaluation feedback path.

This candidate is selected because it is simpler and less flexible than the rejected
histogram approach. The selection is an engineering design choice, not an empirical
claim that the method will pass.

### 3. Fresh evidence is required before fitting

A new immutable fixture set must be created for the redesign protocol. It must have a
new fixture-set ID, version, manifest, scenario-family registry, and split declaration.

At minimum, it must contain:

```text
development_diagnostic observations: 24 or more
calibration observations: 60 or more
fresh_final_evaluation observations: 30 or more
```

The `calibration` and `fresh_final_evaluation` assets must be disjoint at the
scenario-family level, not only the case-ID level. `STF-004`, `STF-005`, and `STF-006`
must not be copied, transformed, truncated, relabelled, or otherwise reused as data in
the new calibration or final-evaluation sets.

The resulting evidence remains synthetic controlled evidence unless a later, separately
governed Kaggle trace source is introduced.

### 4. Fitting and promotion are predeclared

The temperature parameter may be fitted only on the new `calibration` split.

Before fitting begins, the implementation must freeze:

- optimizer and objective;
- confidence clipping behavior;
- valid temperature bounds;
- tie handling;
- artifact serialization format;
- feature schema version;
- minimum observation count;
- fixed evaluation bins for ECE;
- report schema;
- promotion criteria;
- failure taxonomy;
- conservative fallback behavior.

The fresh final-evaluation outcomes are unavailable to the fitting path, optimizer,
candidate-selection logic, report-threshold selection, and policy implementation.

### 5. Promotion remains narrow and does not authorize runtime control

The redesigned artifact may be marked `promotable_for_adaptive_policy_research` only
when all of the following are true on the fresh final-evaluation split:

1. Input manifest, split identity, and artifact provenance validate.
2. Calibration observation count meets the predeclared minimum.
3. Calibrated Brier score is strictly lower than raw-confidence Brier score.
4. Calibrated ECE is strictly lower than raw-confidence ECE using the frozen binning.
5. The transformation is monotonic and preserves confidence ordering.
6. No required report provenance field is missing.
7. No split-leakage or causal-safety failure is present.

Promotion authorizes only the next research phase: implementation and evaluation of a
causal adaptive scheduling policy under separately governed capacity and utility
contracts. It does not authorize runtime control, production claims, throughput claims,
or a policy-winner claim.

### 6. Failure is retained and blocks progression

Any failure must emit a typed status and retain the report. At minimum, the redesigned
protocol must distinguish:

```text
insufficient_calibration_evidence
calibration_fit_failed
calibrator_regression
calibrator_no_strict_improvement
evaluation_split_leakage
artifact_fixture_mismatch
report_provenance_missing
confidence_not_fit_for_automated_scheduling
```

A non-promotion outcome blocks adaptive-policy implementation for that artifact and
fixture set. It must not be corrected by changing the artifact using the same final
evaluation labels.

## Consequences

### Positive consequences

- Preserves the integrity of the original held-out result.
- Converts a negative result into an explicit engineering gate rather than a hidden
  failure.
- Prevents a flexible artifact from being selected because it happens to match a
  four-observation final fixture.
- Creates a low-complexity, inspectable candidate method for the next controlled test.
- Establishes a clear protocol for a new fixture proposal, manifest review, and later
  implementation work.

### Costs and constraints

- No adaptive policy may be built in the current slice.
- The project must author fresh fixtures and provenance before fitting another artifact.
- The new protocol adds a minimum evidence requirement and deliberately slows result
  generation.
- A second negative result remains possible and must be retained.

## Alternatives considered

### Retune the existing histogram calibrator

Rejected. Any post-result change to bins, fallback behavior, or selection rules would
use `STF-004` as a tuning signal and invalidate its held-out role.

### Choose a more flexible calibrator immediately

Rejected. Isotonic regression, subgroup calibration, position-specific parameters, and
multi-stage ensembles introduce flexibility that is not justified by the currently
available controlled evidence. They can be considered only through a future protocol
with independently sufficient calibration evidence.

### Skip calibration and build the adaptive scheduler anyway

Rejected. The PRD requires calibration fitness before confidence-driven automated
control. Proceeding would violate the project’s phase gate and turn a blocked research
result into unsupported behavior.

### Declare calibration permanently impossible

Rejected. The current result is scoped to one frozen histogram artifact and one governed
assessment. It is evidence against that artifact, not a universal impossibility claim.

## Required follow-on artifacts

Before any redesigned fit is implemented, create and review:

```text
1. A new fixture proposal archive or committed fixture-design document.
2. A scenario-family split registry.
3. A new immutable manifest with hashes and counts.
4. Typed contract changes for the temperature artifact and report, if required.
5. Tests that prove no final-evaluation outcome reaches the fit path.
6. A final-evaluation report schema with explicit promotion and non-promotion states.
```

## Claims after this ADR

### Permitted

- The prior histogram calibrator was assessed on its governed held-out fixture and was
  not promoted.
- `STF-004` is quarantined from redesign and tuning.
- The next candidate method and its evidence/promotion protocol are now predeclared.
- SpecSafe remains at held-out replay evaluated maturity for calibration assessment only.

### Forbidden

- The temperature-scaling candidate is better than the histogram artifact.
- Confidence is fit for automated scheduling.
- A causal adaptive policy exists or is authorized.
- Any production throughput, latency, cost, losslessness, or serving claim.
- Any claim that `STF-004` may be reused to validate a redesigned artifact.

## Acceptance criteria

This ADR is complete when:

- it is committed with the associated protocol document;
- no implementation or fixture mutation accompanies this documentation-only slice;
- the protocol identifies the candidate method, required fresh evidence, split
  quarantine, promotion gate, and failure response;
- future implementation work can point to this ADR rather than relying on the previous
  held-out result as informal tuning guidance.
