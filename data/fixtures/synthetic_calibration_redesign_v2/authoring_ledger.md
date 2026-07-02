# V2 Scenario-Family Registry Authoring Ledger

## Status

```text
fixture_set_id=synthetic-calibration-redesign-v2
fixture_set_version=1.0.0
candidate_artifact=bounded-platt-scaling-v1
registry_proposal_status=retained_as_reviewed_provenance
registry_status=finalized_for_case_contract_authoring
v2_case_contracts_status=implemented_no_fixture_assets
v2_runtime_or_outcome_assets_authored=false
v2_manifest_status=not_authorized
v2_fitting_status=not_authorized
v2_final_evaluation_status=not_authorized
v2_adaptive_policy_status=blocked
v2_runtime_control_status=not_eligible
```

## Finalization decision

The reviewed V2 proposal is now hash-linked to `scenario_family_registry.json`. Finalization preserves
all reviewed family IDs, case ranges, split assignments, source-template fingerprints, quarantine flags,
rationales, and target failure modes. It changes no case count, trace design, confidence value, token ID,
or outcome label because none exists at this boundary.

The finalized registry is authoritative for future V2 case membership. The retained proposal remains
provenance evidence and cannot be silently rewritten without causing a proposal-hash mismatch.

## Typed case-contract boundary

The V2 codebase now contains strict in-memory contracts for future runtime inputs and expected outcomes.
Those contracts establish schema, split, role, provenance, minimum context count, replay alignment, and
visible-prefix requirements. They do not load files, write files, generate manifests, fit calibration, or
assess evidence.

Runtime contracts reject evaluation-only fields through schema strictness. Expected outcomes retain labels
only after the runtime contract exists. A replay case may be checked against the finalized registry only
when a later authoring slice supplies both typed objects.

## Scope controls retained

- No V2 runtime-input case file exists.
- No V2 expected-outcome file or label exists.
- No V2 calibration or final-evaluation manifest exists.
- No V2 fitting, assessment, scheduler, capacity, utility, or runtime-control behavior exists.
- No V1 data-bearing asset may be used to create a V2 fixture or test expectation.
- V2 final-evaluation families remain quarantined before any V2 fitting path exists.

## Next authoring gate

The next permitted engineering activity is a separate V2 runtime-and-outcome fixture-authoring slice.
It must create runtime and expected-outcome assets separately, use only finalized V2 case IDs, preserve
the four-context observation minimum, and add loader/registry membership tests. It must not fit or assess
bounded Platt scaling.
