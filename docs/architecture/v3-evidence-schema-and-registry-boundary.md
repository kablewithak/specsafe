# V3 Evidence Schema and Registry Boundary

## Status

Implemented schema-only boundary.

## Purpose

This boundary makes the V3 plan enforceable before any V3 data exists. It reserves the V3 case inventory, validates its split counts, and rejects any V3 fixture root that contains runtime inputs, outcome labels, manifests, fitted artifacts, or another unapproved file.

## What exists

- a strict `CalibrationRedesignV3ScenarioFamilyRegistry` contract;
- a fixed reservation of 36 calibration, 24 final-evaluation, and 8 adversarial cases;
- four quarantined final capacity families, each with six cases and a 2/2/2 workload mix;
- a loader that checks the schema-only root before loading metadata;
- explicit rejection of V1/V2 case and calibrator references in the registry bytes.

## What does not exist

- V3 runtime inputs;
- V3 outcome labels;
- V3 manifests;
- V3 fitting, calibration, policy, capacity-profile, scoring, or reporting code;
- a V3 performance or promotion claim.

## Boundary rule

The allowed fixture-root files are exactly:

```text
scenario_family_registry.json
PROPOSAL_MANIFEST.md
authoring_ledger.md
```

Any directory, JSON artifact, case input, outcome file, manifest, artifact, or report causes the schema-only loader to fail.

## Next authorised step

Create V3 **calibration** case pairs only. Final-evaluation and adversarial case bytes remain prohibited until later governed boundaries.
