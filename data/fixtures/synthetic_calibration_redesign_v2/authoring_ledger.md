# V2 Scenario-Family Registry Authoring Ledger

## Status

```text
fixture_set_id=synthetic-calibration-redesign-v2
fixture_set_version=1.0.0
candidate_artifact=bounded-platt-scaling-v1
registry_proposal_status=proposed_pending_review
v2_runtime_or_outcome_assets_authored=false
v2_manifest_status=not_authorized
v2_fitting_status=not_authorized
v2_final_evaluation_status=not_authorized
v2_adaptive_policy_status=blocked
v2_runtime_control_status=not_eligible
```

## Scope boundary

This ledger accompanies an identifier-and-lineage proposal only. It reserves V2 case identifiers,
scenario-family identities, split assignments, and source-template fingerprints before any fixture
byte is authored.

The proposal is deliberately separate from V1. V1 is retained only as the categorical fact that it
closed without promotion. No V1 data-bearing material was used as an authoring input.

## Proposed family inventory

| Family | Split | Reserved cases | Quarantined | Purpose |
|---|---|---:|---:|---|
| `CRV2-DEV-CONTRACT-BOUNDARIES` | development | 2 | No | Contract and provenance plumbing only. |
| `CRV2-CAL-GLOBAL-ORDINAL` | calibration | 4 | No | Global monotonic calibration coverage. |
| `CRV2-CAL-CROSS-CONTEXT` | calibration | 4 | No | Global calibration across permitted contexts without subgroup parameters. |
| `CRV2-CAL-DOMAIN-BOUNDARIES` | calibration | 4 | No | Confidence-domain and clipping-provenance coverage. |
| `CRV2-FINAL-DISTRIBUTION-SHIFT` | final evaluation | 3 | Yes | Independent held-out global-reliability assessment. |
| `CRV2-FINAL-LOCAL-DISAGREEMENT` | final evaluation | 3 | Yes | Independent held-out local-reliability assessment. |
| `CRV2-FINAL-ORDER-PERTURBATION` | final evaluation | 3 | Yes | Independent held-out order-perturbation assessment. |
| `CRV2-ADV-SPLIT-LINEAGE` | adversarial regression | 1 | No | Cross-split and quarantine-bypass regression coverage. |

## Evidence-floor accounting

The proposal reserves 12 calibration cases and 9 final-evaluation cases. Future authored cases must
supply at least four lawful observation contexts each. That minimum would satisfy the predeclared
floors of at least 48 calibration observations and at least 36 final-evaluation observations.

This is an observation budget, not authored trace content. It contains no confidence values,
candidate IDs, labels, token sequences, prompts, or outcome patterns.

## Accepted design decisions

| Decision | Reason | Boundary preserved |
|---|---|---|
| Reserve all V2 family and case IDs before fixture authoring. | Prevents case selection after labels, fits, or assessments exist. | Authoring remains auditable. |
| Use three calibration and three final-evaluation families. | Meets V2 floor with distinct diagnostic roles. | Final evidence stays independent of fitting. |
| Quarantine every final-evaluation family immediately. | Final cases must be unavailable to fitting before any bytes exist. | Prevents evaluation-to-fit leakage. |
| Keep the candidate global-only. | `bounded-platt-scaling-v1` has no family-specific parameters. | Prevents hidden subgroup calibration. |
| Reserve an adversarial split-lineage family. | Split, fingerprint, and quarantine failures need dedicated regression coverage. | Makes leakage detection testable later. |

## Explicit exclusions

- No runtime-input case file exists in this proposal.
- No expected-outcome file or label exists in this proposal.
- No confidence value, token ID, prompt text, trace sequence, or fixture byte exists in this proposal.
- No manifest, fitting code, assessment code, policy code, capacity profile, utility scorer, or
  runtime-control behavior is created.
- No V1 data-bearing asset may be used to turn this proposal into a V2 fixture or test expectation.

## Next authoring gate

The next permitted slice is a V2 typed registry and fixture-contract implementation boundary. It must
make the proposal schema enforceable without authoring valid runtime or expected-outcome fixture
assets. Only after that contract boundary is merged may separate V2 runtime/outcome authoring begin.
