# Calibration Redesign V2 Entry Protocol

## Status

```text
protocol_status=entry-boundary-approved
fixture_set_id=synthetic-calibration-redesign-v2
candidate_method_status=not_selected
fixture_authoring_status=not_authorized
fitting_status=not_authorized
final_evaluation_status=not_authorized
adaptive_policy_status=blocked
runtime_control_status=not_eligible
```

## Purpose

Define the fixed evidence and sequencing rules for a successor calibration experiment after
the closure of `synthetic-calibration-redesign-v1`.

This is not an implementation plan for a new artifact. It does not authorize method search,
new fixtures, fitting, held-out scoring, or adaptive-policy work.

## V2 physical and type boundaries

Future V2 assets must be isolated from V1 by path, namespace, manifest type, and evidence
identity.

```text
fixture_root=data/fixtures/synthetic_calibration_redesign_v2/
runtime_inputs=data/fixtures/synthetic_calibration_redesign_v2/inputs/cases/
expected_outcomes=data/fixtures/synthetic_calibration_redesign_v2/expected_outcomes/
registry=data/fixtures/synthetic_calibration_redesign_v2/scenario_family_registry.json
calibration_manifest=data/fixtures/synthetic_calibration_redesign_v2/calibration_manifest.json
final_manifest=data/fixtures/synthetic_calibration_redesign_v2/final_evaluation_manifest.json
source_namespace=specsafe.traces.calibration_redesign_v2
```

V2 must not reuse V1 manifest classes as an unmodified type alias. Shared low-level contracts
may be reused only where they remain split-neutral and do not accept V1 data by default.

## Non-negotiable evidence isolation

V2 authoring, fitting, and assessment must not read or import V1 data-bearing assets:

```text
synthetic_calibration_redesign/inputs/
synthetic_calibration_redesign/expected_outcomes/
synthetic_calibration_redesign/manifest.json
synthetic_calibration_redesign/final_evaluation_manifest.json
evidence/calibration/logit-temperature-scaling-v1/
```

Historical V1 ADRs may be cited only for categorical constraints:

```text
v1_closed=true
v1_artifact_not_promoted=true
v1_adaptive_policy_blocked=true
```

They may not supply numeric targets, candidate ranking, fixture-selection rules, or
acceptance-criterion changes.

## Minimum V2 evidence floor

The final counts must be approved before any V2 outcomes are written.

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

These are diagnostic floors, not a generalization claim. A case may be added only with a
documented failure mode, lineage rationale, and non-duplication justification.

## Split and lineage rules

Every V2 family must declare:

```text
scenario_family_id
split
primary_data_role
parent_scenario_family_id
source_template_fingerprint
case_ids
rationale
is_final_evaluation_quarantined
```

Required rules:

1. Calibration and final-evaluation families use disjoint source-template fingerprints.
2. A case ID belongs to exactly one V2 family and one V2 split.
3. Final-evaluation families are quarantined before V2 fitting begins.
4. Runtime input and expected-outcome assets are separate files.
5. Runtime assets contain no post-hoc labels, candidate token IDs, or future-bearing values.
6. Calibration manifests discover only calibration evidence.
7. Final manifests discover only final-evaluation evidence.
8. The fitter accepts only a verified V2 calibration-manifested fixture-set.
9. The held-out evaluator accepts only a verified V2 final-manifested fixture-set.
10. No test may use V1 held-out metrics or labels as V2 expected values.

## Predeclared assessment posture

The V2 candidate artifact must be assessed once, read-only, on the V2 final-evaluation
manifest. The assessment protocol must be frozen before V2 fitting.

The promotion gate must require all of the following:

```text
calibrated_brier_score < raw_brier_score
calibrated_expected_calibration_error < raw_expected_calibration_error
monotonic_transform=true
artifact_provenance_complete=true
manifest_provenance_complete=true
no_split_leakage=true
```

A passing result may authorize only a later adaptive-policy research-design boundary. It does
not authorize a scheduler, policy utility claim, runtime control, or production claim.

## Failure handling

Any V2 non-promotion must be retained without tuning against the V2 final-evaluation corpus.

At minimum, the future V2 result taxonomy must include:

```text
insufficient_calibration_evidence
calibration_fit_failed
calibrator_regression
calibrator_no_strict_improvement
evaluation_split_leakage
artifact_fixture_mismatch
report_provenance_missing
confidence_not_fit_for_automated_scheduling
```

## Next gate

The next permitted artifact is:

```text
docs/architecture/calibration-redesign-v2-method-selection-gate.md
```

It must select one candidate method, define its fixed fit behavior, and record why the
selection does not depend on V1 outcome values. Until that gate is accepted, V2 fixture
authoring is prohibited.
