# V5 Frozen Calibration Corpus Manifest

## Active boundary

V5 calibration-case authoring is complete. `calibration_manifest.json` now freezes the exact
calibration-only evidence inventory before any bounded monotone-beta fitting begins.

```text
CSV5-101..CSV5-148
48 calibration case pairs
96 immutable source assets
192 calibration observations
```

The manifest records a SHA-256 and byte count for every runtime-input and expected-outcome asset,
the aggregate corpus hash, each case-pair relationship, and the SHA-256 of the pre-freeze V5
registry. The active registry carries the canonical manifest hash and the matching pre-freeze
registry hash.

## Present assets

```text
scenario_family_registry.json
PROPOSAL_MANIFEST.md
authoring_ledger.md
calibration_manifest.json
inputs/cases/CSV5-101.json .. CSV5-148.json
expected_outcomes/cases/CSV5-101.json .. CSV5-148.json
```

## Quarantine and exclusions

- `CSV5-201..CSV5-236` final-evaluation reservations remain quarantined.
- `CSV5-301..CSV5-312` adversarial-regression reservations remain quarantined.
- The frozen calibration corpus may support only the predeclared globally shared bounded
  monotone-beta fit-diagnostics stage next.
- No V5 calibration artifact, fit diagnostics, final-evaluation asset, final-evaluation manifest,
  scheduler, capacity profile, utility scorer, policy comparison, or final assessment exists yet.
- No V1–V4 data-bearing evidence was used to select or author V5 assets.

## Next authorised artifact

`v5-bounded-monotone-beta-fit-diagnostics`
