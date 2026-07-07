# V5 Frozen Calibration Corpus and Fit Diagnostics

## Active boundary

The V5 calibration corpus is frozen and its one predeclared globally shared bounded
monotone-beta fit has been retained as calibration-only evidence.

```text
CSV5-101..CSV5-148
48 calibration case pairs
96 immutable source assets
192 calibration observations

artifact_id=bounded-monotone-beta-calibration-v5
artifact_version=1.0.0
optimizer=deterministic_projected_gradient_descent_v1
fit_scope=calibration_only
```

The frozen corpus remains anchored by `calibration_manifest.json`. The retained artifact and
fit diagnostics identify that exact manifest, its aggregate asset hash, and the V5 protocol.
The fit is a fixed method execution, not a held-out promotion decision.

Calibration-only diagnostic floats are persisted at 12 decimal places using an explicit
round-half-even rule. This is a cross-runtime serialization control for hash stability; it does
not round, replace, or retune the retained calibration artifact parameters.

## Present assets

```text
scenario_family_registry.json
PROPOSAL_MANIFEST.md
authoring_ledger.md
calibration_manifest.json
bounded_monotone_beta_calibration_artifact.json
bounded_monotone_beta_calibration_fit_diagnostics.json
inputs/cases/CSV5-101.json .. CSV5-148.json
expected_outcomes/cases/CSV5-101.json .. CSV5-148.json
```

## Calibration-only diagnostics

```text
final_parameters:
  a=0.4842569647145243
  b=0.38665164489663356
  c=0.11190947100094854

calibration_brier_improvement=0.028167911622
calibration_ece_10_bin_improvement=0.134801039864
calibration_auroc_delta=0.0
monotonicity_verification=passed
```

These are calibration-split diagnostics only. They do not establish V5 final eligibility, an
adaptive-policy advantage, capacity behavior, throughput, latency, cost reduction, or runtime
control eligibility.

## Quarantine and exclusions

- `CSV5-201..CSV5-236` final-evaluation reservations remain quarantined.
- `CSV5-301..CSV5-312` adversarial-regression reservations remain quarantined.
- No V5 final-evaluation runtime or outcome asset, final manifest, or held-out assessment exists.
- No V5 scheduler, baseline comparison, capacity profile, utility scorer, or runtime control is
  authorised.
- No V1–V4 data-bearing evidence was used to select, fit, or evaluate V5 assets.

## Next authorised artifact

`v5-final-evaluation-fixture-authoring`
