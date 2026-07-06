# ADR-0014: Charter V4 Around Complete, Testable Final-Gate Semantics

- **Status:** Accepted
- **Date:** 2026-07-06
- **Decision owner:** Kabo Molefe
- **Applies from:** `main` after PR #57 (`6a1ed4f`)
- **Depends on:** ADR-0001, ADR-0002, ADR-0009, ADR-0010, ADR-0013
- **Supersedes:** Nothing. This is a fresh-programme entry charter; it does not alter or overwrite V3 evidence.

## Context

SpecSafe V3 produced a retained, write-once held-out calibration diagnostic result over its frozen 24-case / 96-observation final corpus. The result showed an improvement in the retained Brier and 10-bin expected calibration error diagnostics.

ADR-0013 reconciled a material gate-completeness mismatch: V3's implemented final assessor did not calculate or retain every criterion required by ADR-0010. In particular, the final result was missing the required AUROC ranking-safety criterion and did not enforce ADR-0010's declared minimum Brier/ECE improvement thresholds in the implemented protocol.

The V3 result remains retained evidence. It is not a complete V3 calibration-gate pass and it does not authorize scheduler implementation, policy comparison, capacity-policy tuning, or runtime-control claims.

A fresh V4 programme is justified only if its final-gate contract is complete, executable, and testable **before** any V4 case bytes or held-out outcomes exist.

## Decision

Create V4 as a fresh evidence programme with a gate-completeness-first sequence.

V4 must not author calibration or final-evaluation fixtures, fit a calibrator, write a scheduler, or run a held-out assessment until all requirements in this ADR are merged and reproducible.

V4 retains the same north-star research question:

> Under controlled trace replay, can a valid verification policy use calibrated, decision-time confidence and declared capacity conditions more usefully than blunt fixed rules without using forbidden future information?

V4 does **not** inherit V3 final-case bytes, V3 final labels, V3 final metrics, or V3 calibration artifact parameters as inputs to tuning or fixture design.

## V4 Required Sequence

```text
1. V4 gate-completeness charter                     <-- this ADR
2. V4 method and evidence constitution
3. V4 final-assessment contract and non-final test harness
4. V4 fixture schema and fresh data reservation
5. V4 calibration-only fixture authoring
6. V4 calibrator fit and calibration-only diagnostics
7. V4 final-evidence authoring and immutable manifest freeze
8. One-time V4 final held-out calibration assessment
9. Only if complete V4 gate passes: baselines and causal policy comparison
10. Adversarial regression assets, reports, and public proof
```

No step may be skipped because a prior version produced favorable diagnostics.

## Non-Negotiable V4 Gate-Completeness Requirements

### 1. One typed, machine-readable gate result

Before V4 evidence authoring, the repository must contain a strict result contract that records every criterion required for promotion.

The result must include:

```text
- protocol_id and schema_version
- fixture-set identity and version
- final-manifest and calibration provenance hashes
- exact case and observation counts
- raw and calibrated Brier score
- raw and calibrated fixed-bin ECE
- raw and calibrated AUROC or a documented equivalent ranking metric
- aggregate and per-position metrics
- per-position observation counts
- one boolean/status per gate criterion
- final gate status
- promotion eligibility
- runtime-control eligibility
- refit/per-policy-execution flags
- write-once provenance
```

A result cannot report a passing promotion status unless every required criterion is present, internally consistent, and satisfied.

### 2. Fixed criteria before V4 final evidence exists

The V4 method constitution must predeclare, before V4 final case authoring:

```text
- calibration method and parameters
- minimum final observation count
- minimum Brier-score improvement
- minimum ECE improvement
- ranking-safety tolerance for calibrated versus raw AUROC
- minimum per-position coverage
- policy fallback behavior
- valid baseline set
- policy-comparison score
- result labels and promotion rule
```

V4 may choose new values only through an accepted ADR before any V4 final evidence is authored. It may not tune those values after observing V4 final outcomes.

### 3. Final-gate code must be proven without touching V4 final evidence

Before V4 final fixture authoring, the repository must contain non-final tests proving that the final-assessment code:

```text
- rejects a missing required metric;
- rejects a result missing AUROC/ranking evidence;
- rejects a result whose Brier/ECE values pass but ranking safety fails;
- rejects insufficient per-position coverage;
- rejects a provenance mismatch;
- rejects calibration refit during final assessment;
- rejects scheduler/policy execution during calibration assessment;
- rejects a write destination that already exists before loading/scoring;
- emits deterministic canonical JSON from identical approved non-final test inputs;
- cannot mark runtime control eligible from calibration evidence alone.
```

These tests must use synthetic test fixtures or constructed typed test objects only. They must not load, score, or reveal V4 final evidence.

### 4. Determinism means testable implementation determinism, not a second final run

V4 must distinguish two ideas:

- **Implementation determinism:** proven before final evidence exists through canonical serialization and non-final test fixtures.
- **Final-evidence execution:** a single governed write-once assessment after the immutable final manifest is frozen.

V4 must not require a second live run of the final corpus merely to prove byte identity. The final assessment runner must instead:

```text
- verify all frozen input hashes before scoring;
- reject an existing result destination before loading final cases;
- serialize canonical JSON;
- include all provenance fields required to audit the one recorded result.
```

### 5. V4 gate status is fail-closed

The complete V4 calibration gate must yield one of the following statuses:

```text
PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE
CALIBRATOR_REGRESSION
INSUFFICIENT_HELD_OUT_COVERAGE
RANKING_SAFETY_REGRESSION
INCOMPLETE_GATE_EVIDENCE
INVALID_PROVENANCE
```

Any status other than `PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE` must produce:

```text
adaptive_policy_research_eligibility=blocked
runtime_control_eligible=false
fallback=CONSERVATIVE_FALLBACK
```

A passing calibration gate may permit controlled policy-research implementation only. It must not authorize runtime control, serving, production claims, or claims of policy advantage.

## V4 Evidence Isolation Rules

V4 is a fresh evidence programme.

The following are prohibited as V4 fitting, tuning, or fixture-design inputs:

```text
- V1 or V2 data-bearing assets and metrics
- V3 calibration case/outcome bytes
- V3 final case/outcome bytes
- V3 final held-out metric values
- V3 calibrator bins or artifact parameters
- post-hoc V3 threshold choices
```

The following V3 information may be retained only as engineering process lessons:

```text
- final-gate completeness must be executable before held-out authoring;
- write-once final assessment must reject repeat execution before scoring;
- tests must prove every required result field and gate transition;
- a favorable partial diagnostic is not a promotion decision.
```

## Prohibited Work Until the V4 Gate Contract Is Complete

```text
- Do not author V4 case assets.
- Do not reserve V4 final case identifiers in a way that implies a method choice.
- Do not fit a V4 calibrator.
- Do not create a V4 final-evaluation manifest.
- Do not write V4 scheduler or baseline-policy code.
- Do not implement V4 capacity curves or policy scoring.
- Do not create Kaggle or UI work.
- Do not claim V4 is underway beyond governance and contract preparation.
```

## Acceptance Criteria for the Next V4 Slice

The next implementation slice after this ADR may begin only when it delivers a V4 method-and-evidence constitution that:

1. selects one V4 calibration method and one valid policy family before data exists;
2. states the full calibration gate, including ranking safety and coverage;
3. defines conservative fallback and promotion boundaries;
4. defines a fixed baseline set and replay score;
5. separates calibration, final evaluation, and adversarial regression roles;
6. names the V4 assessment contract and non-final test harness as required before V4 fixture authoring;
7. makes no V4 performance, calibration, or policy-success claim.

## Consequences

### Positive

- V4 cannot repeat V3's incomplete promotion gate.
- The next final assessment will be auditable from one typed result rather than inferred from partial fields.
- Future policy work will be blocked by code if calibration evidence is incomplete.
- One-time final-evaluation discipline remains intact.

### Costs

- V4 begins more slowly because gate semantics and testability come before fixtures.
- A V4 final result may still fail; failure remains valid evidence.
- This ADR deliberately prevents a fast path from V3's retained diagnostics to scheduler work.

## Claims After This ADR

### Permitted

- SpecSafe has retained V3 calibration diagnostics and formally reconciled their non-authorizing scope.
- SpecSafe has a governed V4 entry charter that requires complete, testable final-gate semantics before V4 data authoring.

### Forbidden

- V3 validated a scheduler or policy advantage.
- V4 calibration, scheduler, or capacity evidence exists.
- V4 final data or a V4 final assessment exists.
- Any runtime-control or production-serving claim.

## Final Control Statement

> V4 begins with an executable gate, not another dataset. A final score is useful only when every required criterion, provenance check, fallback behavior, and promotion boundary was fixed and tested before the final evidence could be observed.
