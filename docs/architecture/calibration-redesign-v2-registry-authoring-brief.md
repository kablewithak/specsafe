# V2 Scenario-Family Registry Authoring Brief

## Purpose

Define the only permitted registry-planning artifact after the V2 candidate-method selection gate:
a reviewed scenario-family registry proposal for
`synthetic-calibration-redesign-v2`.

This brief authorizes identifier and lineage planning only. It does not authorize runtime inputs,
expected outcomes, labels, manifests, source code, fitting, or held-out evaluation.

## Current proposal state

```text
candidate_artifact=bounded-platt-scaling-v1
registry_proposal_path=data/fixtures/synthetic_calibration_redesign_v2/scenario_family_registry_proposal.json
registry_proposal_status=proposed_pending_review
v2_runtime_or_outcome_assets_authored=false
```

The proposal reserves V2 scenario-family and case IDs before any fixture content exists. It remains
a proposal until reviewed and merged.

## Required proposal inventory

The registry proposal must meet these predeclared floors before any case bytes are authored:

```text
development_families>=1
development_cases>=2

calibration_families>=3
calibration_cases_per_family>=4
calibration_observations>=48

final_evaluation_families>=3
final_evaluation_cases_per_family>=3
final_evaluation_observations>=36

adversarial_regression_families>=1
```

The proposal must reserve sufficient cases to meet the observation floor without creating duplicate
or non-diagnostic source templates.

## Required registry fields

Each proposed family must declare:

```text
scenario_family_id
split
primary_data_role
parent_scenario_family_id
source_template_fingerprint
reserved_case_ids
rationale
target_failure_modes
is_final_evaluation_quarantined
authoring_status=proposed
```

No outcome value, confidence value, token ID, prompt text, trace sequence, or fixture byte may
appear in this proposal.

## Required split posture

```text
development:
  role=synthetic_fixture
  final_quarantined=false

calibration:
  role=calibration
  final_quarantined=false

final_evaluation:
  role=held_out_evaluation
  final_quarantined=true

adversarial_regression:
  role=synthetic_fixture
  final_quarantined=false
```

Calibration and final-evaluation source-template fingerprints must be disjoint. No V1 fingerprint,
trace shape, token sequence, confidence band, label pattern, case identifier, or case-count
balancing rationale may be reused.

## Candidate-method compatibility

The proposal must identify how its calibration-family coverage can diagnose a global bounded Platt
transform without adding candidate-method features. The registry must not create:

```text
workload_specific_calibration_parameter
position_specific_calibration_parameter
subgroup_calibration_parameter
capacity_conditioned_calibration_parameter
policy_action
threshold_label
utility_label
```

## Rejected-case ledger

The proposal must include a rejected-case ledger that records at least:

- near-duplicate source-template ideas;
- cases that would recreate V1 trace structures;
- cases whose labels would be ambiguous or non-diagnostic;
- cases requiring outcome-dependent authoring;
- cases whose final-evaluation status could be inferred from calibration balancing.

## Acceptance gate

A registry proposal is acceptable only when:

1. all V2 family IDs and reserved case IDs are unique;
2. all splits and primary roles are coherent;
3. final families are quarantined before any V2 fitting;
4. calibration and final fingerprints are disjoint;
5. the proposal contains no fixture bytes or outcome labels;
6. the proposal demonstrates coverage of the predeclared evidence floor;
7. the proposal does not use V1 data-bearing evidence;
8. the next step after acceptance is a V2 typed registry and fixture-contract implementation
   boundary, not valid V2 fixture authoring or fitting.

## Non-claims

This brief and its proposal do not claim that V2 fixtures exist, bounded Platt scaling will pass,
or confidence is fit for automated scheduling.
