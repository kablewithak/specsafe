# V2 Proposal-Only Contract Boundary

## Purpose

Convert the reviewed V2 scenario-family registry proposal into a strict local contract before any
V2 case byte, outcome label, manifest, fitting artifact, or assessment report can exist.

The boundary is implemented by:

```text
src/specsafe/traces/calibration_redesign_v2.py
tests/test_calibration_redesign_v2.py
```

## Enforced model boundary

`CalibrationRedesignV2ScenarioFamilyRegistryProposal` accepts only planning metadata for:

```text
fixture_set_id=synthetic-calibration-redesign-v2
candidate_artifact_id=bounded-platt-scaling-v1
proposal_status=accepted_for_contract_enforcement
v1_data_bearing_evidence_used=false
v2_runtime_or_outcome_assets_authored=false
```

It validates reserved V2 IDs, split-to-role coherence, final-evaluation quarantine, globally unique
source-template fingerprints, family and case floors, and observation-budget floors.

## Root-asset boundary

`assert_calibration_redesign_v2_proposal_only_fixture_root(...)` permits the V2 proposal JSON and
planning documents. It rejects:

- any file under `inputs/` or `expected_outcomes/`;
- `calibration_manifest.json` or `final_evaluation_manifest.json`;
- any JSON file other than `scenario_family_registry_proposal.json`.

This is intentionally temporary. A later controlled-registry finalization slice must replace it with
explicit runtime/outcome contracts and an approved asset layout before valid V2 cases can be loaded.

## Typed failures

```text
calibration_redesign_v2_proposal_schema_error
calibration_redesign_v2_proposal_provenance_mismatch
calibration_redesign_v2_v1_evidence_reference
calibration_redesign_v2_proposal_only_boundary_violation
```

## Non-claims

This boundary does not author V2 fixture data, fit bounded Platt scaling, evaluate V2 calibration,
select a policy threshold, compare scheduling policies, or authorize adaptive scheduling or runtime
control.
