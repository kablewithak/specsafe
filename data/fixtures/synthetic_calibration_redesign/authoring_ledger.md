# Calibration Redesign Fixture Authoring Ledger

## Status

```text
fixture_set_id=synthetic-calibration-redesign-v1
fixture_set_version=1.0.0
status=registry-governed; calibration-corpus-frozen; calibration-artifact-fitted; final-evaluation-corpus-frozen; final-manifest-authored; heldout-assessment-complete; calibrator-rejected; adaptive-policy-blocked
candidate_calibrator=logit-temperature-scaling-v1
historical_heldout_case=STF-004 permanently excluded
```

## Accepted design decisions

| Decision | Reason | Evidence boundary preserved |
|---|---|---|
| Reserve `CRV1-001` through `CRV1-012` before case authoring. | IDs can be reviewed before runtime inputs or outcomes exist. | Prevents final-evaluation reshuffling after fitting. |
| Use two calibration families with three cases each. | Meets the governed diagnostic floor for fresh fitting evidence. | Calibration has no dependence on `STF-004`. |
| Use two quarantined final-evaluation families with two cases each. | Meets the governed held-out floor while keeping independent scenario templates. | Final evidence remains separate from fitting. |
| Store source-template fingerprints in the registry. | Makes family-level leakage testable instead of relying on filename conventions. | Blocks cross-split template reuse. |
| Retain runtime inputs and expected outcomes as separate assets. | The runtime boundary must not expose observed labels. | Preserves causal replay discipline. |
| Author `CRV1-009` and `CRV1-010` only under the predeclared `CRV1-FINAL-MIXED-RELIABILITY` family. | The family was registered as final evaluation and quarantined before any case bytes existed. | Prevents a calibration case from being relabelled as held-out evidence. |
| Author `CRV1-011` and `CRV1-012` only under the predeclared `CRV1-FINAL-ABRUPT-SUFFIX` family. | The family was registered as final evaluation and quarantined before any case bytes existed. | Prevents final-evaluation case selection from being influenced by temperature-fit results. |
| Build `final_evaluation_manifest.json` only after both final families exist. | The final inventory must be complete before held-out assessment begins. | Blocks partial, selectively assembled final evaluation. |
| Keep final manifests distinct from calibration manifests and fitting types. | Final cases must be immutable assessment inputs, never fitting inputs. | Blocks temperature search and refitting through manifest discovery and runtime type checks. |
| Apply the frozen `logit-temperature-scaling-v1` artifact once to the final manifest. | Promotion requires a read-only held-out assessment rather than in-sample improvement. | Blocks final evidence from fitting, retuning, or selection. |
| Reject promotion when calibrated Brier score regresses, even though ECE improves. | The predeclared gate requires both metrics not to worsen. | Blocks metric shopping and false-positive promotion. |

## Final-evaluation authoring record

| Case | Workload | Trace intent | Quarantine condition |
|---|---|---|---|
| `CRV1-009` | Structured text | Mixed reliability with a high-confidence rejection after an earlier rejected position. | Runtime input excludes candidate IDs and observed labels; outcomes stay post-hoc. |
| `CRV1-010` | Open-ended chat | Mixed reliability with a low-confidence rejection and later accepted token after prefix failure. | Runtime input excludes candidate IDs and observed labels; outcomes stay post-hoc. |
| `CRV1-011` | Code | Strong early confidence followed by an abrupt low-confidence suffix and consecutive rejection. | Runtime input excludes candidate IDs and observed labels; outcomes stay post-hoc. |
| `CRV1-012` | Open-ended chat | Early confidence followed by an abrupt low-confidence suffix, including a later accepted token after prefix failure. | Runtime input excludes candidate IDs and observed labels; outcomes stay post-hoc. |

## Final-manifest boundary

- `final_evaluation_manifest.json` inventories only `final_evaluation` / `held_out_evaluation` case assets.
- It requires all predeclared quarantined final case IDs from the scenario-family registry.
- Each declared runtime and outcome byte stream is hash-addressed with a deterministic aggregate hash.
- The final manifested fixture-set type is intentionally distinct from the calibration manifested fixture-set type.
- The temperature fitter rejects the final manifested fixture-set before it can read labels or temperature-search inputs.

## Held-out assessment result

```text
final_evaluation_manifest_aggregate_sha256=be496cf719780e39b248b51d7d994ab8bafc3780d9abf5b094c86ba6d684831c
assessed_case_ids=CRV1-009,CRV1-010,CRV1-011,CRV1-012
observation_count=18
raw_brier_score=0.1420388888888889
calibrated_brier_score=0.14320093951851715
brier_improvement=-0.0011620506296282362
raw_expected_calibration_error=0.2483333333333333
calibrated_expected_calibration_error=0.20896181673124276
expected_calibration_error_improvement=0.03937151660209054
status=calibrator_regression
promotion_decision=not_promoted_calibrator_regression
adaptive_policy_research_eligibility=blocked_held_out_calibration_regression
artifact_refit=false
artifact_mutated=false
```

The expected calibration error improved, but calibrated Brier score regressed. The predeclared
gate therefore rejects the artifact and blocks adaptive-policy research.

## Explicit exclusions

- `STF-004` is historical evidence only. It must not appear in this fixture set, registry,
  manifest, inputs, outcomes, fit selection, final assessment selection, or a future redesign.
- `CRV1-009` through `CRV1-012` must not be added to any calibration manifest, fitting
  selection, temperature-search routine, threshold selection, policy configuration, or v2
  fixture-design process.
- The frozen v1 artifact, fit report, final manifest, and held-out assessment are immutable
  evidence. They must not be rewritten to alter the recorded promotion decision.
- No adaptive policy, capacity profile, utility scorer, scheduler, or runtime-control work is
  authorized from `synthetic-calibration-redesign-v1`.

## Next valid gate

The v1 experiment is closed as a reproducible negative result. Any future work must either:

1. package this result as an audit-grade reliability proof; or
2. begin a new `synthetic-calibration-redesign-v2` with new calibration cases, new
   final-evaluation cases, new source-template fingerprints, a predeclared candidate method,
   and a new read-only final assessment.

The v1 held-out outcomes are consumed historical evidence and must not tune, select, or design
the v2 experiment.
