# V3 Calibration Position-Spread Fixtures

## Purpose

`CRV3-CAL-POSITION-SPREAD` adds fresh V3 calibration evidence for the fixed four-position verification contract. It complements curve coverage by showing that confidence quality can differ as a candidate block gets longer.

## Authorised case range

- Case IDs: `CRV3-113` through `CRV3-124`
- Split: `calibration`
- Cases: 12
- Candidate positions per case: 4
- Observations: 48
- Runtime/outcome file pairs: 12 pairs

## What is deliberately varied

Each case contains one lawful runtime context for each position from one through four. The runtime confidences descend across both case difficulty and candidate position. The separate outcome files contain a controlled decline in conditional acceptance:

| Candidate position | Accepted observations | Total observations |
|---|---:|---:|
| 1 | 10 | 12 |
| 2 | 8 | 12 |
| 3 | 6 | 12 |
| 4 | 3 | 12 |

The result is a diagnostic synthetic calibration family, not a claim about real model behaviour.

## Safety boundary

- Runtime inputs contain only lawful pre-sample context, raw confidence, and visible-prefix state.
- Candidate token IDs and acceptance labels live only in the separate outcome files.
- No final-evaluation or adversarial-regression bytes exist in this slice.
- No V3 manifest, fitted calibrator, capacity profile, policy implementation, score, or promotion decision is added.
- No V1 or V2 data-bearing evidence is used.

## Regression intent

Tests must reject a final-evaluation file appearing early, an unreserved V3 case, a missing outcome file, an outcome label in a runtime file, an invalid visible prefix, a changed position count, or a changed position-level acceptance shape.

## Next boundary

The next permitted data slice is `CRV3-CAL-WORKLOAD-MIX`, `CRV3-125` through `CRV3-136`. The V3 final and adversarial sets remain absent.
