# V2 Scenario-Family Registry Authoring Ledger

## Status

```text
fixture_set_id=synthetic-calibration-redesign-v2
fixture_set_version=1.0.0
candidate_artifact=bounded-platt-scaling-v1
registry_proposal_status=accepted_for_contract_enforcement
v2_contract_boundary_status=enforced
v2_runtime_or_outcome_assets_authored=false
v2_manifest_status=not_authorized
v2_fitting_status=not_authorized
v2_final_evaluation_status=not_authorized
v2_adaptive_policy_status=blocked
v2_runtime_control_status=not_eligible
```

## Scope boundary

This ledger now accompanies a strict proposal-only contract boundary. The V2 registry reserves
identifiers, split assignments, lineage fingerprints, and observation floors. It still contains no
runtime-input case, expected outcome, label, confidence value, token ID, prompt, or trace byte.

The V2 loader reads only the V2 proposal JSON. It fails closed when it sees V1-style case references,
V2 runtime or outcome assets, V2 manifests, duplicate reserved identifiers, reused fingerprints,
invalid split/role assignment, missing final quarantine, or insufficient reserved observation budget.

## Accepted design decisions

| Decision | Reason | Boundary preserved |
|---|---|---|
| Freeze the proposal under a strict Pydantic contract before case authoring. | Reserved IDs and lineage become testable rather than narrative-only. | Fixture selection remains inspectable. |
| Reject every non-proposal JSON asset inside the V2 fixture root. | A future runtime or outcome asset must enter through a later controlled boundary. | Prevents silent fixture leakage. |
| Keep the V2 module isolated from V1 data-bearing paths. | V1 may be cited only categorically in governance documents. | Blocks V1 outcome-led redesign. |
| Retain three calibration and three final families with their reserved case ranges. | The budget meets the predeclared V2 evidence floors before labels exist. | Prevents post-label family reshaping. |
| Preserve the global-only bounded-Platt candidate. | Families diagnose evidence coverage, not subgroup parameters. | Prevents hidden workload or position calibration. |

## Evidence-floor accounting

The accepted proposal reserves 12 calibration cases and 9 final-evaluation cases. Each future
calibration and final case must contain at least four lawful observation contexts. That retains the
predeclared floors of at least 48 calibration observations and at least 36 final-evaluation
observations.

This accounting is not authored trace content and it is not an outcome target.

## Explicit exclusions

- No V2 runtime-input case file exists.
- No V2 expected-outcome file or label exists.
- No V2 confidence value, token ID, prompt text, trace sequence, or fixture byte exists.
- No V2 manifest, fitter, assessment, policy, capacity profile, utility scorer, or runtime-control
  behavior exists.
- No V1 data-bearing asset may be read by V2 proposal loading, fixture authoring, fitting,
  assessment, or test expectations.

## Next authoring gate

The next permitted slice is controlled V2 registry finalization and case-contract implementation. It
must define strict V2 runtime and expected-outcome models plus registry provenance checks before any
committed V2 case file is accepted. It must not fit or assess `bounded-platt-scaling-v1`.
