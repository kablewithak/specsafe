# ADR-0006: Establish the V2 Calibration Redesign Entry Boundary

- **Status:** Accepted
- **Date:** 2026-07-02
- **Decision scope:** `synthetic-calibration-redesign-v2`
- **Supersedes:** None
- **Does not supersede:** ADR-0005 or any V1 evidence, manifest, fit, assessment, or closure record.

## Context

`synthetic-calibration-redesign-v1` is closed as a reproducible negative result.

The frozen `logit-temperature-scaling-v1` artifact was fit only on `CRV1-001` through
`CRV1-006`, then assessed once against the independent final-evaluation corpus
`CRV1-009` through `CRV1-012`. The read-only assessment retained 18 observations.

```text
status=calibrator_regression
promotion_decision=not_promoted_calibrator_regression
adaptive_policy_research_eligibility=blocked_held_out_calibration_regression
runtime_control_eligibility=not_eligible_pending_adaptive_policy_evaluation
artifact_refit=false
artifact_mutated=false
```

The result is valid negative evidence. It does not establish that every calibration method
will fail. It does establish that V1 must not be repaired in place, and that V1 final
outcomes cannot become a selection or tuning input for a successor.

## Decision

SpecSafe opens a documentation-only V2 redesign entry boundary.

No V2 fixture bytes, outcome labels, manifests, calibration artifact, policy code, capacity
profile, utility scorer, or runtime-control behavior is authorized by this ADR.

The future V2 experiment must use:

```text
fixture_set_id=synthetic-calibration-redesign-v2
fixture_set_root=data/fixtures/synthetic_calibration_redesign_v2/
source_namespace=specsafe.traces.calibration_redesign_v2
```

The candidate method is intentionally **not selected** in this ADR. It must be selected
once, through the V2 method-selection gate, before any V2 runtime input or expected-outcome
asset is authored.

## V1 evidence quarantine

The following V1 assets remain retained only for audit, reproduction, and categorical
historical context:

```text
CRV1-001 through CRV1-012
data/fixtures/synthetic_calibration_redesign/manifest.json
data/fixtures/synthetic_calibration_redesign/final_evaluation_manifest.json
evidence/calibration/logit-temperature-scaling-v1/artifact.json
evidence/calibration/logit-temperature-scaling-v1/fit_report.json
evidence/calibration/logit-temperature-scaling-v1/heldout_assessment.json
```

They must not determine V2:

- candidate-method choice;
- method parameters, priors, search bounds, or fallback behavior;
- confidence clipping or transformation;
- bin count or metric thresholds;
- fixture family design, case count, workload mix, trace shape, confidence bands, token
  sequences, labels, seeds, or balancing;
- policy configuration, capacity behavior, or utility criteria.

V2 code must not load V1 outcome files, V1 manifests, V1 assessment reports, or V1 artifact
files as an input to authoring, fitting, evaluation, promotion, or test expectation.

## Required V2 sequence

```text
1. Approve this V2 entry boundary.
2. Approve one candidate method through the blinded method-selection gate.
3. Register V2 scenario families before authoring V2 case bytes.
4. Author separate V2 runtime and expected-outcome assets.
5. Generate separate immutable calibration and final-evaluation manifests.
6. Fit once using only the V2 calibration manifest.
7. Assess once using only the V2 final-evaluation manifest.
8. Retain either promotion or non-promotion without in-place repair.
```

Any deviation requires a new ADR before implementation.

## Consequences

### Permitted claims

- V1 was closed as a reproducible negative calibration result.
- V2 is governed as a new experiment with a separate fixture root and evidence lineage.
- V1 held-out evidence cannot be repurposed for V2 design or tuning.
- No adaptive policy or runtime control is authorized.

### Forbidden claims

- V2 has a selected calibrator.
- V2 evidence has been authored or evaluated.
- Calibration has improved.
- Confidence is fit for automated verification scheduling.
- Any policy, utility, throughput, cost, latency, customer-data, deployment, or production
  claim.

## Acceptance criteria

This ADR is complete when:

- the V2 namespace and fixture root are reserved in documentation only;
- the V1 quarantine rules are explicit and testable in future implementation;
- the next permitted slice is the V2 method-selection gate, not fixture authoring or fitting;
- no code, fixture, manifest, or assessment evidence is changed in this slice.
