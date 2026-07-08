# V5 Kaggle Trace Replay Attempt 001 Report

## Scope

This report summarizes a local deterministic replay over the first retained Kaggle trace archive.

The replay uses:

- runtime signal: `raw_draft_probability`
- diagnostic label: `target_argmax_matches_candidate`
- retained archive: `specsafe_v5_qwen_trace_collection_v1_attempt_001.zip`
- retained analysis report hash: `1d31f0f0e2ae3e825878289780c4754185d2bd936c4f31eb3de4feda3a385885`

## Retained replay report

- file: `evidence/kaggle-trace-collection/v5-qwen-governed-trace-collection-v1/attempt-001-t4/trace_replay_report.json`
- sha256: `f536120982a616bbae9daf5d9b946469e70348dc52dd5d23af430bd9a5a5ba0f`

## Main threshold observations

- threshold `0.0`: selected `24/24`, match rate `0.625`, nonmatches `9`
- threshold `0.3`: selected `16/24`, match rate `0.8125`, nonmatches `3`
- threshold `0.5`: selected `13/24`, match rate `0.9230769230769231`, nonmatches `1`
- threshold `0.6`: selected `9/24`, match rate `1.0`, nonmatches `0`
- threshold `0.8`: selected `8/24`, match rate `1.0`, nonmatches `0`

## Interpretation

The replay is directionally supportive: higher draft-probability thresholds reduce mismatch risk in this retained sample. The useful trade-off is visible but small-sample.

No threshold is selected. No calibration is fitted. No policy utility claim is made.

## Next authorized step

A calibration/replay harness may be built next, but it must remain diagnostic and must preserve the small-sample boundary.
