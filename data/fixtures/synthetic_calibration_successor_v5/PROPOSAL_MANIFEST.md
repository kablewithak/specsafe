# V5 Calibration Mixed-Reliability Contrast Proposal Manifest

## Active boundary

V5-3e retains the curve-coverage, position-spread, and workload-variation families and
authors only the fresh calibration mixed-reliability-contrast family. The active case pairs are:

```text
CSV5-101..CSV5-148
```

`CSV5-137..CSV5-148` add twelve fresh calibration-only cases with four candidate positions per
case. They balance `structured_text`, `code`, and `open_ended_chat` workloads across four cases
each. Six cases deliberately pair high stated confidence with weak observed acceptance, while six
contrast cases pair lower stated confidence with stronger observed acceptance.

The contrast is a calibration diagnostic only. V5 remains one globally shared bounded
monotone-beta calibration method: no workload-specific parameters, thresholds, or policy rules are
introduced by this slice.

## Present assets

```text
scenario_family_registry.json
PROPOSAL_MANIFEST.md
authoring_ledger.md
inputs/cases/CSV5-101.json .. CSV5-148.json
expected_outcomes/cases/CSV5-101.json .. CSV5-148.json
```

## Quarantine and exclusions

- `CSV5-201..CSV5-236` final-evaluation reservations remain quarantined.
- `CSV5-301..CSV5-312` adversarial-regression reservations remain quarantined.
- No calibration or final-evaluation manifest exists.
- No fitter, artifact, diagnostics, scheduler, capacity profile, utility scorer, policy comparison,
  or final assessment is authorised.
- No V1–V4 data-bearing evidence was used to select or author these assets.

## Next authorised artifact

`v5-calibration-manifest-freeze`
