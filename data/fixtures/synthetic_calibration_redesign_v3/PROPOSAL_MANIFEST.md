# V3 Calibration Curve-Coverage Authoring Manifest

This directory contains exactly the first authorised V3 calibration family.

## Present at this boundary

- `scenario_family_registry.json`
- `PROPOSAL_MANIFEST.md`
- `authoring_ledger.md`
- `inputs/cases/CRV3-101.json` through `CRV3-112.json`
- `expected_outcomes/cases/CRV3-101.json` through `CRV3-112.json`

## What these files are for

The twelve case pairs provide 48 fresh calibration observations across a broad raw-confidence range. They are self-authored synthetic diagnostics for learning the calibration curve only.

Runtime inputs contain only decision-time fields. Candidate token IDs, observed acceptance labels, and prefix-survival labels live only in the separate outcome files.

## Still prohibited

- calibration, final-evaluation, or adversarial manifests;
- any V3 fitted calibration artifact;
- any V3 scheduler or policy code;
- final-evaluation runtime inputs or labels;
- adversarial-regression runtime inputs or labels;
- V1 or V2 data-bearing evidence references.

The next authorised slice may create `CRV3-113` through `CRV3-124` for calibration position-spread coverage only.
