# V2 Scenario-Family Registry Proposal Manifest

## Purpose

This is an application manifest for the reviewed V2 registry proposal. It describes a planning-only
bundle; it is not a runtime fixture manifest and does not authorize loading, fitting, assessment, or
policy control.

## Included files

```text
data/fixtures/synthetic_calibration_redesign_v2/scenario_family_registry_proposal.json
data/fixtures/synthetic_calibration_redesign_v2/authoring_ledger.md
data/fixtures/synthetic_calibration_redesign_v2/rejected_case_ideas.md
docs/architecture/calibration-redesign-v2-registry-proposal.md
docs/architecture/calibration-redesign-v2-registry-authoring-brief.md
```

## Required review checks

1. Family IDs and reserved case IDs are unique.
2. Split and primary data role are coherent.
3. Calibration and final-evaluation fingerprints are disjoint.
4. Every final-evaluation family is quarantined.
5. The calibration budget reserves at least 48 future observations.
6. The final-evaluation budget reserves at least 36 future observations.
7. No runtime inputs, outcomes, labels, confidence values, token IDs, or fixture bytes appear.
8. V1 data-bearing assets are not an authoring input.
9. No code, manifest, fitter, assessor, policy, capacity, utility, or runtime-control artifact is added.

## Non-claims

The proposal does not claim that V2 fixture content exists, that bounded Platt scaling will fit,
that calibration will improve, or that adaptive scheduling is authorized.
