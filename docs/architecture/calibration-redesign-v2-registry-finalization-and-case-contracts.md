# V2 Registry Finalization and Typed Case-Contract Boundary

## Status

```text
fixture_set_id=synthetic-calibration-redesign-v2
registry_status=finalized_for_case_contract_authoring
candidate_artifact=bounded-platt-scaling-v1
v2_runtime_or_outcome_assets_authored=false
v2_manifests_authored=false
v2_fitting_authorized=false
v2_heldout_assessment_authorized=false
```

## Purpose

Convert the reviewed V2 scenario-family proposal into an immutable, hash-linked registry and define the
strict runtime-input and expected-outcome contracts that a later V2 authoring slice must use.

This boundary solves a narrow problem: a future fixture may not silently change family membership, split,
quarantine status, source-template fingerprint, or case identifier after the evidence plan was reviewed.
It does not create any V2 fixture bytes or outcome labels.

## Registry finalization

`scenario_family_registry.json` is valid only when all of the following hold:

- the retained proposal exists at `scenario_family_registry_proposal.json`;
- the registry contains the exact SHA-256 of that proposal's byte stream;
- registry and proposal agree on fixture identity, source type, candidate artifact, observation budget,
  exclusions, family IDs, split roles, case IDs, fingerprints, rationale, failure modes, and quarantine;
- final-evaluation families remain quarantined;
- V2 root contains no runtime input, expected outcome, calibration manifest, or final-evaluation manifest.

The registry changes the reviewed case ranges from proposed reservations to finalized reservations for typed
case-contract authoring. It does not authorize file-backed case loading.

## Runtime-input contract

`CalibrationRedesignV2RuntimeInput` contains only scheduler-visible information:

```text
schema_version
fixture_set_id
fixture_set_version
fixture_id
case_id
trace_id
request_id
scenario_family_id
split
data_role
source_type
generation_note
contexts
```

The contract is strict. Candidate token IDs, observed-acceptance labels, prefix-survival labels, metrics,
promotion states, and any extra fields are rejected. Each future V2 runtime case requires at least four
ordered causal contexts with trace and request identity alignment.

## Expected-outcome contract

`CalibrationRedesignV2ExpectedOutcomes` is structurally separate and is the only contract that can retain
post-hoc candidate token IDs, observed acceptance, and prefix-survival labels. It requires at least four
contiguous outcomes per authored case and validates cumulative prefix survival within each decode round.

A `CalibrationRedesignV2ReplayCase` joins the contracts only after both parse successfully. It verifies
metadata and position-key equality and checks that every runtime visible prefix is exactly the historical
candidate-token prefix from the post-hoc outcome asset.

## Registry membership boundary

A replay case may be validated against only the exact finalized V2 registry type. Its case ID, family ID,
split, and data role must match a reserved registry record. This membership check has no file loader and no
manifest discovery path at this stage.

## V1 and lifecycle isolation

The V2 registry and case-contract modules do not import V1 fixture manifests, V1 outcome assets, V1 fitted
artifacts, or V1 held-out reports. V1 remains categorical historical evidence only.

No V2 calibration manifest, final-evaluation manifest, bounded-Platt fitting code, artifact, assessment,
policy, capacity profile, utility scorer, or runtime control exists after this boundary.

## Next authorized boundary

The next engineering slice may author typed V2 runtime and expected-outcome fixture assets from the finalized
case inventory. It must use separate files and preserve the four-observation floor. It must not fit,
evaluate, tune, or promote `bounded-platt-scaling-v1`.
