# Calibration Redesign Fixture Authoring Ledger

## Status

```text
fixture_set_id=synthetic-calibration-redesign-v1
fixture_set_version=1.0.0
status=registry-governed; calibration-corpus-frozen; calibration-artifact-fitted; final-evaluation-corpus-frozen; final-manifest-authored; heldout-assessment-pending
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

## Explicit exclusions

- `STF-004` is historical evidence only. It must not appear in this fixture set, registry, manifest, inputs, outcomes, fit selection, or final assessment selection.
- `CRV1-009` through `CRV1-012` must not be added to any calibration manifest, fitting selection, temperature-search routine, threshold selection, or policy configuration.
- No held-out calibration score, promotion decision, adaptive policy, capacity profile, utility scorer, or report is created in this slice.
- The frozen temperature artifact must remain unchanged while final-evaluation evidence is manifested and assessed.

## Next assessment gate

Use the frozen `logit-temperature-scaling-v1` artifact against the verified final-evaluation manifest. The assessment must be read-only: no fixture mutation, refitting, temperature search, threshold selection, or policy configuration is permitted.
