# V2 Scenario-Family Registry Authoring Ledger

## Status

```text
fixture_set_id=synthetic-calibration-redesign-v2
fixture_set_version=1.0.0
candidate_artifact=bounded-platt-scaling-v1
registry_proposal_status=retained_as_reviewed_provenance
registry_status=finalized_for_case_contract_authoring
v2_case_contracts_status=implemented
v2_case_asset_authoring_layout_status=implemented
v2_runtime_or_outcome_assets_authored=true
v2_authored_family_count=1_of_8
v2_authored_calibration_family_count=1_of_3
v2_authored_calibration_case_count=4_of_12
v2_authored_calibration_observation_count=16_of_minimum_48
v2_manifest_status=not_authorized
v2_fitting_status=not_authorized
v2_final_evaluation_status=not_authorized
v2_adaptive_policy_status=blocked
v2_runtime_control_status=not_eligible
```

## Authored family: `CRV2-CAL-GLOBAL-ORDINAL`

This ledger records the first V2 fixture-authoring tranche. It adds the four calibration cases
reserved by the finalized registry:

```text
CRV2-101
CRV2-102
CRV2-103
CRV2-104
```

Each case has exactly four separately stored runtime contexts and four expected outcomes. The
runtime assets contain scheduler-visible, pre-sample confidence and capacity information only. The
outcome assets contain candidate token IDs, observed acceptance, and cumulative prefix-survival
labels only. The loader joins them only after independent validation and checks finalized-registry
membership.

The family is intentionally narrow: all cases use the same permitted workload context and capacity
profile so the evidence exercises a globally shared ordinal confidence relationship without a
subgroup feature or context-specific parameter. This is a fixture-design property, not an assertion
that a future bounded-Platt artifact will pass calibration or promotion.

## Registry provenance note

`scenario_family_registry.json` remains an immutable record of the finalization boundary and retains
`v2_runtime_or_outcome_assets_authored=false`. That field describes the state when the reviewed
reservation registry was finalized; it is not rewritten after case authoring. This ledger is the
current inventory record for authored V2 assets.

## Scope controls retained

- No V2 calibration manifest exists.
- No V2 final-evaluation manifest or final-evaluation case asset exists.
- No V2 fitting, artifact, assessment, scheduler, capacity utility, or runtime-control behavior exists.
- No V1 data-bearing case, label, confidence, token sequence, metric, fingerprint, or result informed
  these fixtures or their regression assertions.
- The V2 final-evaluation families remain quarantined.

## Next authoring gate

The next permitted fixture slice is `CRV2-CAL-CROSS-CONTEXT`, cases `CRV2-105` through `CRV2-108`.
It must preserve separate runtime/outcome assets, finalized-registry membership, the four-observation
floor, and V2 final-evaluation quarantine. It must not create a manifest, fit, assess, tune, or
promote bounded Platt scaling.
