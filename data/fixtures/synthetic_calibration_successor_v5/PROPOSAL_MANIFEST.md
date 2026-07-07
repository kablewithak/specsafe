# V5 Calibration Workload-Variation Proposal Manifest

## Active boundary

V5-3d retains the curve-coverage and position-spread families and authors only the fresh
calibration workload-variation family. The active case pairs are:

```text
CSV5-101..CSV5-136
```

`CSV5-125..CSV5-136` add twelve fresh calibration-only cases with four candidate positions per
case. They balance `structured_text`, `code`, and `open_ended_chat` workloads across four cases
each while retaining overlapping confidence bands and distinct observed-outcome mixes.

The workload labels are diagnostic provenance. V5 remains a single globally shared bounded
monotone-beta calibration method: no workload-specific parameters, thresholds, or policy rules are
introduced by this slice.

## Present assets

```text
scenario_family_registry.json
PROPOSAL_MANIFEST.md
authoring_ledger.md
inputs/cases/CSV5-101.json .. CSV5-136.json
expected_outcomes/cases/CSV5-101.json .. CSV5-136.json
```

## Quarantine and exclusions

- `CSV5-137..CSV5-148` remain reserved and unauthored.
- `CSV5-201..CSV5-236` final-evaluation reservations remain quarantined.
- `CSV5-301..CSV5-312` adversarial-regression reservations remain quarantined.
- No calibration or final-evaluation manifest exists.
- No fitter, artifact, diagnostics, scheduler, capacity profile, utility scorer, policy comparison,
  or final assessment is authorised.
- No V1–V4 data-bearing evidence was used to select or author these assets.

## Next authorised artifact

`v5-calibration-mixed-reliability-contrast-fixtures`
