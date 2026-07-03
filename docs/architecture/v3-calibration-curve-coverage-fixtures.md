# V3 Calibration Curve-Coverage Fixtures

## Status

**Active authoring boundary.**

This document records the first data-bearing V3 slice. It authors only the calibration family `CRV3-CAL-CURVE-COVERAGE` and leaves every final-evaluation and adversarial-regression asset absent.

## Purpose

The future V3 calibration method is fixed as `quantile-isotonic-calibration-v1`. It needs fresh raw-confidence observations that cover a broad range rather than a narrow cluster.

This slice provides:

```text
12 self-authored synthetic calibration cases
4 candidate positions per case
48 calibration observations
raw-confidence coverage from 0.10 through 0.87
```

## Runtime versus outcome separation

Every case has two files:

```text
inputs/cases/CRV3-###.json
expected_outcomes/cases/CRV3-###.json
```

The runtime file contains only the values a future decision system could see before it decides. It contains no candidate token IDs, acceptance labels, or prefix-survival labels.

The outcome file contains those post-hoc fields for later scoring and calibration fitting only.

## Curve shape

The 48 observations are deliberately distributed across four raw-confidence bands. The observed acceptance rate rises as confidence rises, but not in a straight line. That creates a realistic controlled reason to test the already selected isotonic calibration method later.

This is not a result claim. No V3 calibration fit, hidden test, policy score, or promotion decision exists at this boundary.

## Isolation rules

- `CRV3-201` through `CRV3-224` remain absent and quarantined.
- `CRV3-301` through `CRV3-308` remain absent.
- No V3 manifest is allowed yet.
- No V3 policy or scheduler code is allowed yet.
- V1 and V2 data-bearing evidence remains prohibited.

## Next authorised step

Author calibration position-spread cases `CRV3-113` through `CRV3-124`. Do not create final or adversarial case bytes.
