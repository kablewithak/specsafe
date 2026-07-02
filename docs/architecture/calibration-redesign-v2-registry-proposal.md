# V2 Scenario-Family Registry Proposal

## Status

```text
proposal_status=proposed_pending_review
fixture_set_id=synthetic-calibration-redesign-v2
candidate_artifact=bounded-platt-scaling-v1
proposal_scope=identifier_and_lineage_only
runtime_or_outcome_assets_authored=false
manifest_generation_authorized=false
fitting_authorized=false
held_out_assessment_authorized=false
adaptive_policy_authorized=false
runtime_control_eligible=false
```

## Purpose

This proposal converts the approved V2 registry authoring brief into a reviewable reserved
scenario-family inventory. It is intentionally authored before V2 fixture bytes, labels, or code so
future fitting and held-out assessment remain interpretable.

The proposal selects no new method. It is compatible only with the already selected global
`bounded-platt-scaling-v1` candidate.

## Proposed coverage

| Split | Families | Reserved cases | Future observation budget | Control |
|---|---:|---:|---:|---|
| development | 1 | 2 | Not used for fit or final assessment. | Synthetic fixture only. |
| calibration | 3 | 12 | At least 48. | Fitting evidence only. |
| final evaluation | 3 | 9 | At least 36. | Quarantined assessment evidence only. |
| adversarial regression | 1 | 1 | Regression only. | Leakage and provenance coverage. |

Future case bytes may not reduce these floors. Each calibration and final-evaluation case must
eventually contribute at least four lawful observation contexts, but this proposal deliberately
contains no trace sequences, confidence values, token IDs, prompts, or labels.

## Split and lineage controls

- Every family has a reserved unique ID and a unique proposed source-template fingerprint.
- Calibration-family fingerprints and final-evaluation-family fingerprints are disjoint.
- Final-evaluation families are marked quarantined before any V2 fitting code or asset exists.
- All family records have `parent_scenario_family_id=null`; no cross-split lineage is proposed.
- The adversarial family exists to later prove rejection of fingerprint reuse, cross-split case
  assignment, and final-quarantine bypasses.
- The selected calibration artifact remains global-only. No family is a vehicle for workload,
  position, scenario, capacity, or subgroup-specific parameters.

## V1 isolation statement

This proposal was authored without using V1 data-bearing assets. It does not reuse historical case
identifiers, fingerprints, trace shapes, prompts, token sequences, confidence values, labels,
metrics, bin occupancies, fit outputs, or balancing rationales.

V1 may be cited only as the categorical reason a fresh, independent V2 experiment is necessary.

## Review acceptance criteria

The proposal is ready to merge when the accompanying JSON and ledgers demonstrate:

1. the predeclared V2 family and observation floors;
2. unique family IDs, case IDs, and fingerprints;
3. split-role coherence;
4. final-family quarantine;
5. absence of fixture content and outcome labels;
6. absence of V1 data-bearing inputs;
7. no fitting, assessment, policy, or runtime-control scope.

## Next authorized artifact

A V2 typed registry and fixture-contract implementation boundary. It must enforce the proposal
without creating any valid V2 runtime or expected-outcome case asset.
