# SpecSafe V4 Evidence Reservation Manifest

## Purpose

This root reserves the complete V4 evidence plan before any V4 case data exists. It is a schema-only boundary, not a source of runtime inputs, expected outcomes, labels, manifests, calibration artifacts, or policy results.

## Fixed reservation

| Split | Cases | Positions per case | Observations | Current state |
|---|---:|---:|---:|---|
| Calibration | 48 | 4 | 192 | Reserved only |
| Final evaluation | 36 | 4 | 144 | Reserved and quarantined |
| Adversarial regression | 12 | 4 | 48 | Reserved and quarantined |

The exact family and case-ID reservation is recorded in `scenario_family_registry.json`.

## Physical boundary

At this stage the fixture root may contain only:

```text
PROPOSAL_MANIFEST.md
authoring_ledger.md
scenario_family_registry.json
```

It must not contain directories, case assets, outcome labels, manifests, artifacts, reports, or final-assessment output.

## Current authorization

The V4 final-assessment contract and non-final tests are merged. The next authorized artifact is the first calibration-only family, `v4-calibration-curve-coverage-fixtures`.

Final-evaluation and adversarial case bytes remain quarantined.
