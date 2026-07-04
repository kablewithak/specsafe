# V3 Calibration Workload-Mix Fixtures

## Purpose

`CRV3-CAL-WORKLOAD-MIX` completes the fresh V3 calibration corpus with controlled workload variation. It adds separate self-authored cases for structured text, code, and open-ended chat so the later frozen calibration method is not fitted only to one type of task.

## Authorised case range

- Case IDs: `CRV3-125` through `CRV3-136`
- Split: `calibration`
- Cases: 12
- Candidate positions per case: 4
- Observations: 48
- Runtime/outcome file pairs: 12

## Controlled workload shape

Each workload receives four cases and sixteen observations. The family deliberately creates different confidence and acceptance patterns by workload:

| Workload | Cases | Observations | Accepted observations | Mean raw confidence direction |
|---|---:|---:|---:|---|
| `structured_text` | 4 | 16 | 14 | Highest |
| `code` | 4 | 16 | 9 | Middle |
| `open_ended_chat` | 4 | 16 | 5 | Lowest |

This provides a diagnostic workload-confidence shift for calibration. It is controlled synthetic evidence, not a claim about any real model or workload.

## Safety boundary

- Runtime inputs contain only lawful pre-sample context, raw confidence, and visible-prefix state.
- Candidate token IDs and acceptance labels live only in separate outcome files.
- The full 36-case calibration corpus is now authored, but no calibration manifest has been created yet.
- No final-evaluation or adversarial-regression bytes exist in this slice.
- No V3 fitted calibrator, capacity profile, policy implementation, score, or promotion decision is added.
- No V1 or V2 data-bearing evidence is used.

## Regression intent

Tests must reject a final-evaluation file appearing early, an unreserved V3 case, a missing outcome file, an outcome label in a runtime file, an invalid visible prefix, a changed workload balance, a changed workload-level acceptance shape, or an unexpected calibration manifest.

## Next boundary

The next permitted slice creates the deterministic V3 calibration manifest from `CRV3-101` through `CRV3-136`. Final-evaluation and adversarial sets remain absent.
