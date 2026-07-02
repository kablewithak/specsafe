# V2 Scenario-Family Registry Proposal Manifest

## Purpose

This manifest now records the accepted V2 planning contract boundary. It is not a runtime fixture
manifest and does not authorize V2 runtime input, expected outcome, fitting, assessment, policy, or
runtime-control behavior.

## Included contract-boundary files

```text
data/fixtures/synthetic_calibration_redesign_v2/scenario_family_registry_proposal.json
data/fixtures/synthetic_calibration_redesign_v2/authoring_ledger.md
data/fixtures/synthetic_calibration_redesign_v2/rejected_case_ideas.md
docs/architecture/calibration-redesign-v2-registry-proposal.md
docs/architecture/calibration-redesign-v2-registry-authoring-brief.md
docs/architecture/calibration-redesign-v2-contract-boundary.md
src/specsafe/traces/calibration_redesign_v2.py
tests/test_calibration_redesign_v2.py
```

## Enforced review checks

1. Family IDs, reserved case IDs, and source-template fingerprints are unique.
2. Split and primary data role are coherent.
3. Calibration and final-evaluation fingerprints cannot overlap.
4. Every final-evaluation family is quarantined.
5. The calibration budget reserves at least 48 future observations.
6. The final-evaluation budget reserves at least 36 future observations.
7. V1 data-bearing case references are rejected.
8. V2 runtime inputs, expected outcomes, and V2 manifests are rejected at this proposal-only stage.
9. Only `scenario_family_registry_proposal.json` may be a JSON asset in the V2 fixture root.

## Non-claims

The accepted proposal contract does not create V2 fixtures, does not fit bounded Platt scaling, does
not assess calibration, and does not authorize adaptive scheduling or runtime control.
