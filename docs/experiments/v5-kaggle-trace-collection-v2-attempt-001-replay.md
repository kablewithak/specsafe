# V5 Kaggle Trace Collection V2 Attempt 001 Replay Diagnostic

## Status

```text
collection_id=v5-qwen-governed-trace-collection-v2
attempt_id=attempt-001-t4
report_id=v5_qwen_trace_collection_v2_attempt_001_replay
status=diagnostic_replay_only
```

## Purpose

This report records deterministic local threshold replay over the retained second
Kaggle trace archive. It reads only committed retained artifacts and does not
rerun Kaggle model inference.

## Input evidence

```text
runtime_records=120
expected_outcome_records=120
case_count=30
target_argmax_matches=97
target_argmax_nonmatches=23
```

## Diagnostic observations

The replay signal is directionally supportive but not promoted:

| Threshold | Selected | Matches | Nonmatches | Selected match rate |
|---:|---:|---:|---:|---:|
| 0.0 | 120 | 97 | 23 | 0.8083333333333333 |
| 0.3 | 84 | 76 | 8 | 0.9047619047619048 |
| 0.4 | 73 | 72 | 1 | 0.9863013698630136 |
| 0.5 | 64 | 64 | 0 | 1.0 |
| 0.8 | 40 | 40 | 0 | 1.0 |

The threshold frontier is useful evidence for the next diagnostic gate, but this
slice does not select, tune, or promote any threshold.

## Evidence boundary

This is deterministic local replay only.

It does not:

- fit a Kaggle-derived calibrator
- tune or promote thresholds
- promote scheduler utility
- publish public artifacts
- claim production speedup, latency, throughput, cost savings, or production readiness

## Next safe gate

The next safe slice is the v2 calibration diagnostic/readiness gate. Calibration
fitting remains blocked until that gate explicitly authorizes it.
