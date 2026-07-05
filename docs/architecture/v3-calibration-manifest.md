# V3 Calibration Manifest

## Purpose

This boundary freezes the complete V3 calibration corpus before `quantile-isotonic-calibration-v1` is fitted.

The manifest contains exactly:

- 36 calibration case pairs: `CRV3-101` through `CRV3-136`;
- 72 evidence files: one runtime input and one separate expected-outcome file per case;
- 144 calibration observations across four positions per case;
- three calibration families, with 12 cases each;
- SHA-256 hashes and byte counts for every case asset; and
- the registry hash and byte count used to establish the inventory.

## Boundary

The manifest builder may read only:

- `scenario_family_registry.json`;
- `inputs/cases/CRV3-101.json` through `CRV3-136.json`; and
- `expected_outcomes/cases/CRV3-101.json` through `CRV3-136.json`.

It must not read or create V3 final-evaluation or adversarial-regression assets. It does not fit a calibration method, choose a threshold, run a policy, or make a promotion decision.

## Next authorised work

The next separate boundary may fit `quantile-isotonic-calibration-v1` against this frozen manifest. The frozen corpus must not be reshaped after fitting begins.
