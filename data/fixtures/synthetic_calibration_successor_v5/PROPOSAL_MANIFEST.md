# V5 Calibration Position-Spread Proposal Manifest

## Active boundary

V5-3c retains the curve-coverage family and authors only the fresh calibration
position-spread family. The active case pairs are:

```text
CSV5-101..CSV5-124
```

`CSV5-113..CSV5-124` add twelve fresh calibration-only cases with four candidate positions
per case. Their confidence values decline from position one through position four, creating a
diagnostic position-spread signal without freezing a calibration manifest or fitting V5.

## Present assets

```text
scenario_family_registry.json
PROPOSAL_MANIFEST.md
authoring_ledger.md
inputs/cases/CSV5-101.json .. CSV5-124.json
expected_outcomes/cases/CSV5-101.json .. CSV5-124.json
```

## Quarantine and exclusions

- `CSV5-125..CSV5-148` remain reserved and unauthored.
- `CSV5-201..CSV5-236` final-evaluation reservations remain quarantined.
- `CSV5-301..CSV5-312` adversarial-regression reservations remain quarantined.
- No calibration or final-evaluation manifest exists.
- No fitter, artifact, diagnostics, scheduler, capacity profile, utility scorer, policy comparison,
  or final assessment is authorised.
- No V1–V4 data-bearing evidence was used to select or author these assets.

## Next authorised artifact

`v5-calibration-workload-variation-fixtures`
