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
v2_authored_family_count=4_of_8
v2_authored_calibration_family_count=3_of_3
v2_authored_calibration_case_count=12_of_12
v2_authored_calibration_observation_count=48_of_minimum_48
v2_authored_final_evaluation_family_count=1_of_3
v2_authored_final_evaluation_case_count=3_of_9
v2_authored_final_evaluation_observation_count=12_of_minimum_36
v2_manifest_status=calibration_manifest_frozen; final_evaluation_manifest_not_created
v2_fitting_status=frozen_calibration_only_artifact_retained
v2_final_evaluation_status=case_authoring_in_progress; assessment_not_authorized
v2_adaptive_policy_status=blocked
v2_runtime_control_status=not_eligible
```

## Authored family: `CRV2-CAL-GLOBAL-ORDINAL`

The first V2 fixture-authoring tranche added the four calibration cases reserved by the finalized
registry:

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

## Authored family: `CRV2-CAL-CROSS-CONTEXT`

The second V2 fixture-authoring tranche added the four calibration cases reserved by the finalized
registry:

```text
CRV2-105
CRV2-106
CRV2-107
CRV2-108
```

The cases retain separate runtime and expected-outcome assets, exactly four aligned observations
per case, and finalized-registry membership. They vary permitted workload and synthetic capacity
contexts across structured text, code, and open-ended chat without adding a workload-specific,
position-specific, subgroup, or capacity-conditioned calibration parameter. The selected candidate
remains a single global bounded-Platt transform that may consume only aligned confidence and
acceptance observations after a future calibration manifest is verified.

This cross-context fixture design is diagnostic evidence, not an acceptance result. It does not
claim that a global transform will fit the authored observations or pass later held-out evaluation.
No V2 final-evaluation case is authored in this tranche.

## Authored family: `CRV2-CAL-DOMAIN-BOUNDARIES`

The final calibration fixture tranche adds the four cases reserved by the finalized registry:

```text
CRV2-109
CRV2-110
CRV2-111
CRV2-112
```

The cases complete the predeclared V2 calibration evidence floor: 12 cases and 48 separate,
aligned observations. They exercise raw confidence values immediately below, equal to, and above
the fixed future bounded-Platt clipping epsilon of `0.000001`, and analogously near
`1 - 0.000001`. Every runtime confidence remains strictly inside the lawful open interval `(0, 1)`.
The runtime contract contains no clipping field or transformed probability: clipping is fixed future
fitter behavior, not scheduler-visible runtime metadata.

All four cases retain one permitted workload context and one synthetic capacity snapshot so the
family diagnoses numeric-domain handling without introducing a workload-specific,
position-specific, subgroup, or capacity-conditioned calibration parameter. Their expected outcomes
are stored only in separate post-hoc assets. This family is evidence for a later manifest-verified
fit; it does not claim that clipping, bounded Platt scaling, or the future candidate artifact passes
calibration or promotion.

## Registry provenance note

`scenario_family_registry.json` remains an immutable record of the finalization boundary and retains
`v2_runtime_or_outcome_assets_authored=false`. That field describes the state when the reviewed
reservation registry was finalized; it is not rewritten after case authoring. This ledger is the
current inventory record for authored V2 assets.

## Scope controls retained

- No V2 calibration manifest exists in this slice.
- No V2 final-evaluation manifest or final-evaluation case asset exists.
- No V2 fitting, artifact, assessment, scheduler, capacity utility, or runtime-control behavior exists.
- No V1 data-bearing case, label, confidence, token sequence, metric, fingerprint, or result informed
  these fixtures or their regression assertions.
- The V2 final-evaluation families remain quarantined.

## Next authorized boundary

The next slice may create and verify a calibration-only V2 manifest over the 12 authored calibration
case pairs. It must not author V2 final-evaluation case bytes, fit or tune bounded Platt scaling,
inspect final-evaluation outcomes, or introduce scheduler, capacity-utility, or runtime-control
behavior.


## Calibration manifest freeze — 2026-07-03

- Added `calibration_manifest.json` for the complete committed V2 calibration corpus only.
- The manifest inventories `CRV2-101` through `CRV2-112` as 12 paired runtime/outcome cases,
  retaining 48 authored observations across the three reserved calibration families.
- Each manifest entry records the exact repository-relative path, SHA-256 digest, and byte count.
- The manifest is linked to the exact finalized `scenario_family_registry.json` bytes and its
  aggregate hash covers the complete inventory.
- Final-evaluation case IDs (`CRV2-201` through `CRV2-209`), final-evaluation manifests, fitting,
  assessment, scheduler behavior, capacity utility, and runtime control remain prohibited.
- This is a fixture-integrity boundary only. It neither fits nor evaluates
  `bounded-platt-scaling-v1`.

## Calibration-only bounded-Platt fit freeze — 2026-07-03

- Added deterministic calibration-only fitting for the preselected
  `bounded-platt-scaling-v1` candidate.
- The fitter consumed only the verified `calibration_manifest.json` and the 12 committed V2
  calibration case pairs. It did not access V2 final-evaluation material.
- Retained immutable evidence under `evidence/calibration/bounded-platt-scaling-v1/`:
  - `artifact.json`
  - `fit_report.json`
- The frozen artifact records the V2 calibration-manifest aggregate SHA-256, all 12 fit case IDs,
  the three calibration scenario-family IDs, sample and label counts, fixed optimizer settings,
  bounds, convergence state, fitted global slope and intercept, and calibration-only loss values.
- The fit report remains explicitly non-promotional:
  `final_evaluation_accessed=false`, `promotion_status=not_assessed`, and
  `runtime_control_eligible=false`.
- This in-sample calibration fit is not a held-out result. It does not establish V2 calibration
  success, adaptive-policy eligibility, scheduler value, capacity benefit, or runtime-control
  eligibility.

## Next authorized boundary

The next slice may author the three V2 final-evaluation scenario families reserved by the
finalized registry, retaining their held-out quarantine from calibration fitting. It must not
refit, tune, alter, or select the frozen bounded-Platt artifact after final-evaluation outcomes
exist. It must create separate runtime and expected-outcome assets, then later a distinct
final-evaluation manifest, before one read-only held-out assessment can occur.

## Authored held-out family: `CRV2-FINAL-DISTRIBUTION-SHIFT`

The first quarantined V2 final-evaluation tranche adds the three cases reserved by the
finalized registry:

```text
CRV2-201
CRV2-202
CRV2-203
```

Each case retains four separately stored runtime contexts and four post-hoc expected outcomes,
for 12 held-out observations in total. The family is deliberately kept within one permitted
workload context and one synthetic capacity snapshot so that it exercises an independent global
reliability-shift condition rather than adding a workload, capacity, or policy parameter.

The frozen calibration manifest remains calibration-only and continues to enumerate exactly
`CRV2-101` through `CRV2-112`. The frozen bounded-Platt artifact and fit report are not
modified, refit, retuned, selected, or scored in this slice. The held-out runtime JSON contains
only pre-sample context; candidate token IDs, observed acceptance, and prefix-survival labels
remain physically separate in expected-outcome JSON.

No V2 final-evaluation manifest exists yet. No V2 held-out assessment, promotion decision,
scheduler behavior, capacity utility result, or runtime-control claim is authorized.

## Next authorized boundary

The next slice may author `CRV2-FINAL-LOCAL-DISAGREEMENT` cases `CRV2-204` through
`CRV2-206`. It must preserve the frozen calibration manifest and artifact, must not create a
final-evaluation manifest, and must not score or use held-out outcomes to change any fit or
policy behavior.
