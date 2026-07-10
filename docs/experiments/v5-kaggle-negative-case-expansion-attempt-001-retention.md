# V5 Kaggle Negative-Case Expansion Attempt 001 Retention

## Status

Retained archive for `v5-qwen-negative-case-expansion-v1 / attempt-001-t4`.

This is a Kaggle-environment-measured trace archive from the targeted negative-case expansion run. It is retained for deterministic local analysis, replay, and combined calibration-readiness diagnostics.

## Retained archive

- Archive: `evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/attempt-001-t4/specsafe_v5_qwen_negative_case_expansion_v1_attempt_001_t4.zip`
- Archive SHA-256: `557c7519aa6012c4770d9e24df1e15815a3295447f3eac2080b1b28c511c601e`
- Source commit: `cd238e3e84391585be01e635ce74c4d400ba2dce`
- Collection ID: `v5-qwen-negative-case-expansion-v1`
- Attempt ID: `attempt-001-t4`
- Trace schema version: `kaggle_trace_collection_v2`

## Measured result

| Metric | Value |
|---|---:|
| Runtime records | 64 |
| Expected outcome records | 64 |
| Cases | 16 |
| Target argmax matches | 51 |
| Target argmax nonmatches | 13 |
| Target argmax match rate | 0.796875 |

## Why this matters

The v2 calibration diagnostic was blocked because the retained v2 archive had only 23 observed nonmatches against the minimum 30 negative-count readiness floor.

This negative-case expansion produced 13 additional nonmatches. On raw count, the combined v2 plus negative-case pool now has:

- Combined records: 184
- Combined matches: 148
- Combined nonmatches: 36

That resolves the prior negative-count shortfall on raw count. Calibration fitting is still not authorized by this retention slice. A separate combined diagnostic gate must verify joins, bins, metrics, and readiness before any calibration-fitting slice.

## Retained files

The archive and extracted artifacts are retained together:

- `runtime_records.jsonl`
- `expected_outcome_records.jsonl`
- `timing_records.jsonl`
- `trace_summary.json`
- `environment_report.json`
- `retention_manifest.json`

## Evidence boundary

This retention slice does not:

- rerun Kaggle model inference
- analyze confidence distributions beyond archive-retention checks
- fit a Kaggle-derived calibrator
- tune or promote thresholds
- promote scheduler utility
- publish public artifacts
- claim production speedup, latency, throughput, cost savings, or production readiness

## Next safe gate

After merge, the next safe slice is deterministic local analysis and replay over the retained negative-case archive, followed by a combined calibration-readiness diagnostic across the v2 archive and this negative-case archive.
