# V5 Frozen Calibration and Held-Out Assessment Boundary

## Active boundary

V5 calibration evidence remains frozen and the retained bounded monotone-beta fit remains
calibration-only evidence. The complete held-out corpus is now independently frozen:

```text
CSV5-201..CSV5-236
36 held-out case pairs
72 source assets
144 observations
```

The final held-out corpus spans four separate diagnostic families:

```text
CSV5-201..CSV5-209  curve coverage
CSV5-210..CSV5-218  position spread
CSV5-219..CSV5-227  workload variation
CSV5-228..CSV5-236  mixed-reliability contrast
```

## Present frozen evidence

```text
scenario_family_registry.json
PROPOSAL_MANIFEST.md
authoring_ledger.md
calibration_manifest.json
bounded_monotone_beta_calibration_artifact.json
bounded_monotone_beta_calibration_fit_diagnostics.json
final_evaluation_manifest.json
final_evidence_index.json
inputs/cases/CSV5-101.json .. CSV5-148.json
expected_outcomes/cases/CSV5-101.json .. CSV5-148.json
final_evaluation/inputs/cases/CSV5-201.json .. CSV5-236.json
final_evaluation/expected_outcomes/cases/CSV5-201.json .. CSV5-236.json
```

`final_evaluation_manifest.json` records every held-out file hash, byte count, case pair, family,
and aggregate hash. `final_evidence_index.json` retains a label-free index for inspection and later
assessment provenance.

## Quarantine and exclusions

- `CSV5-301..CSV5-312` remain unauthored adversarial-regression reservations.
- The frozen calibration manifest, calibration artifact, and fit diagnostics remain byte-identical.
- The V5 held-out calibration assessment is retained once as immutable synthetic evidence.
- No threshold selection, scheduler, baseline comparison, capacity profile, utility scorer, policy replay,
  or runtime control result is introduced here.
- No V1–V4 data-bearing evidence was used to select, fit, or evaluate V5 assets.

## Next authorised artifact

`v5-calibrated-causal-load-aware-policy-foundation`
