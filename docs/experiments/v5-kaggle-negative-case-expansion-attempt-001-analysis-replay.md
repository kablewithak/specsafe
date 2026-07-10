# V5 Kaggle Negative-Case Expansion Attempt 001 Analysis and Replay

## Status

This document summarizes deterministic local analysis and replay over the retained
`v5-qwen-negative-case-expansion-v1 / attempt-001-t4` archive.

This is a post-collection diagnostic slice only. It does not rerun Kaggle model
inference, fit a calibrator, tune thresholds, promote scheduler utility, publish
artifacts, or claim production readiness.

## Retained archive

- Collection ID: `v5-qwen-negative-case-expansion-v1`
- Attempt ID: `attempt-001-t4`
- Archive SHA-256: `557c7519aa6012c4770d9e24df1e15815a3295447f3eac2080b1b28c511c601e`
- Source commit: `cd238e3e84391585be01e635ce74c4d400ba2dce`
- Runtime records: `64`
- Expected outcome records: `64`
- Cases: `16`
- Raw prompt text retained: `false`

## Diagnostic findings

- Target argmax matches: `51`
- Target argmax nonmatches: `13`
- Target argmax match rate: `0.796875`
- Mean raw confidence for matches: `0.43474915419139115`
- Mean raw confidence for nonmatches: `0.207277827251416`
- Raw confidence ROC-AUC diagnostic: `0.7918552036199095`
- Brier diagnostic: `0.3137117831119408`
- Fixed-bin ECE diagnostic: `0.4083309590932913`
- Fixed-bin MCE diagnostic: `0.5645891942761161`

The confidence signal remains directionally supportive: accepted records have
higher mean raw confidence than nonaccepted records, and nonaccepted records have
higher mean draft entropy than accepted records.

## Replay preview

Threshold replay remains diagnostic only:

| Threshold | Selected | Matches | Nonmatches | Match rate |
|---:|---:|---:|---:|---:|
| `0.0` | `64` | `51` | `13` | `0.796875` |
| `0.1` | `60` | `50` | `10` | `0.8333333333333334` |
| `0.2` | `46` | `42` | `4` | `0.9130434782608695` |
| `0.3` | `35` | `31` | `4` | `0.8857142857142857` |
| `0.4` | `24` | `23` | `1` | `0.9583333333333334` |
| `0.5` | `17` | `17` | `0` | `1.0` |
| `0.6` | `17` | `17` | `0` | `1.0` |
| `0.7` | `10` | `10` | `0` | `1.0` |
| `0.8` | `5` | `5` | `0` | `1.0` |
| `0.9` | `1` | `1` | `0` | `1.0` |


## Combined raw-count implication

The retained v2 archive had `23` nonmatches. This negative-case archive adds
`13` nonmatches.

Raw combined count after this archive:

- Combined records: `184`
- Combined matches: `148`
- Combined nonmatches: `36`
- Minimum negatives required for calibration fit: `30`
- Negative-count floor crossed on raw count: `true`

This resolves the old negative-count blocker on raw count. It does not authorize
calibration fitting by itself. A separate combined calibration-readiness
diagnostic must verify the joined evidence pool before fitting is allowed.

## Evidence boundary

This slice does not authorize:

- Kaggle model reruns
- calibration fitting
- threshold tuning or promotion
- scheduler promotion
- public release
- production speedup, throughput, latency, cost, or readiness claims

## Next safe gate

After this slice merges, the next safe gate is a combined v2 plus negative-case
calibration-readiness diagnostic.
