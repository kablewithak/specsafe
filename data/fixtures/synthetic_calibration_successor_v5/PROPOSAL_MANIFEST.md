# V5 Frozen Calibration and Complete Quarantined Final Fixture Authoring

## Active boundary

The V5 calibration corpus remains frozen and the one predeclared globally shared bounded
monotone-beta calibration fit remains retained as calibration-only evidence. This stage adds the
fourth and final fresh held-out final-evaluation family:

```text
CSV5-228..CSV5-236
9 held-out mixed-reliability contrast case pairs
18 held-out source assets
36 held-out observations
3 cases per workload
```

Together, the complete authored held-out fixture boundary is now `CSV5-201..CSV5-236`: 36 case
pairs, 72 source assets, and 144 observations. Final assets live exclusively under
`final_evaluation/`. They are not named by `calibration_manifest.json`, are not supplied to the
retained fit, and do not create a final manifest or a held-out result.

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
final_evaluation/inputs/cases/CSV5-201.json .. CSV5-236.json
final_evaluation/expected_outcomes/cases/CSV5-201.json .. CSV5-236.json
```

## Quarantine and exclusions

- `CSV5-201..CSV5-209` are held-out final curve-coverage fixtures.
- `CSV5-210..CSV5-218` are held-out final position-spread fixtures.
- `CSV5-219..CSV5-227` are held-out final workload-variation fixtures.
- `CSV5-228..CSV5-236` are held-out final mixed-reliability contrast fixtures.
- `CSV5-301..CSV5-312` remain unauthored adversarial-regression reservations.
- No V5 final-evaluation manifest, held-out assessment, threshold selection, scheduler,
  baseline comparison, capacity profile, utility scorer, or runtime control is authorised.
- No V1–V4 data-bearing evidence was used to select, fit, or evaluate V5 assets.

## Next authorised artifact

`v5-final-evaluation-manifest-freeze`
