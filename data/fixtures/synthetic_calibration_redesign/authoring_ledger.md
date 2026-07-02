# Calibration Redesign Fixture Authoring Ledger

## Status

```text
fixture_set_id=synthetic-calibration-redesign-v1
fixture_set_version=1.0.0
status=closed-negative-result; calibration-corpus-frozen; final-evaluation-corpus-consumed; manifests-frozen; heldout-assessment-complete
candidate_calibrator=logit-temperature-scaling-v1
promotion_status=not_promoted_calibrator_regression
adaptive_policy_status=blocked_held_out_calibration_regression
runtime_control_status=not_eligible_pending_adaptive_policy_evaluation
historical_heldout_case=STF-004 permanently excluded
```

## Accepted design decisions

| Decision | Reason | Evidence boundary preserved |
|---|---|---|
| Reserve `CRV1-001` through `CRV1-012` before case authoring. | IDs were reviewable before runtime inputs or outcomes existed. | Prevented final-evaluation reshuffling after fitting. |
| Use two calibration families with three cases each. | Met the initial governed diagnostic floor for fitting evidence. | Calibration had no dependence on `STF-004`. |
| Use two quarantined final-evaluation families with two cases each. | Met the initial held-out floor while retaining independent scenario templates. | Final evidence remained separate from fitting. |
| Store source-template fingerprints in the registry. | Made family-level leakage testable instead of relying on filenames. | Blocked cross-split template reuse. |
| Retain runtime inputs and expected outcomes as separate assets. | Runtime input must not expose observed labels. | Preserved causal replay discipline. |
| Keep calibration and final manifests distinct. | Final evidence must not reach the fit path. | Blocked temperature search and refitting through manifest discovery and type checks. |
| Retain the negative held-out result without repair. | Brier score regressed even though ECE improved. | Blocked false-positive promotion from a partial metric improvement. |

## Final-evaluation authoring record

| Case | Workload | Trace intent | Quarantine condition |
|---|---|---|---|
| `CRV1-009` | Structured text | Mixed reliability with a high-confidence rejection after an earlier rejected position. | Runtime input excludes candidate IDs and observed labels; outcomes stay post-hoc. |
| `CRV1-010` | Open-ended chat | Mixed reliability with a low-confidence rejection and later accepted token after prefix failure. | Runtime input excludes candidate IDs and observed labels; outcomes stay post-hoc. |
| `CRV1-011` | Code | Strong early confidence followed by an abrupt low-confidence suffix and consecutive rejection. | Runtime input excludes candidate IDs and observed labels; outcomes stay post-hoc. |
| `CRV1-012` | Open-ended chat | Early confidence followed by an abrupt low-confidence suffix, including a later accepted token after prefix failure. | Runtime input excludes candidate IDs and observed labels; outcomes stay post-hoc. |

## Frozen held-out assessment

```text
final_evaluation_manifest_aggregate_sha256=be496cf719780e39b248b51d7d994ab8bafc3780d9abf5b094c86ba6d684831c
observation_count=18

raw_brier_score=0.1420388888888889
calibrated_brier_score=0.14320093951851715
brier_improvement=-0.0011620506296282362

raw_expected_calibration_error=0.2483333333333333
calibrated_expected_calibration_error=0.20896181673124276
expected_calibration_error_improvement=0.03937151660209054

status=calibrator_regression
promotion_decision=not_promoted_calibrator_regression
```

The V1 artifact is not promoted. The V1 final-evaluation corpus is consumed and may be
inspected only as immutable historical audit evidence.

## Explicit exclusions

- `STF-004` remains historical evidence only and must not appear in V1 or V2 authoring,
  fitting, manifest, assessment, threshold, or policy inputs.
- `CRV1-001` through `CRV1-012` must not be copied, transformed, relabelled, rebalanced,
  truncated, or used as a V2 design or tuning source.
- No V1 artifact, fit report, manifest, final manifest, or held-out report may be overwritten
  to revise the promotion decision.
- No adaptive policy, capacity profile, utility scorer, scheduler, or runtime-control work is
  authorized from this fixture set.

## V2 re-entry reference

The next permissible work is documentation-only V2 method selection under:

```text
fixture_set_id=synthetic-calibration-redesign-v2
governing_adr=docs/adr/ADR-0006-v2-calibration-redesign-entry-boundary.md
method_selection_gate=docs/architecture/calibration-redesign-v2-method-selection-gate.md
```

V2 fixture authoring remains blocked until one candidate method is selected through that gate.
