# Apply Manifest — Independent Holdout Archive Retention

## Slice

```text
branch=feat/retain-independent-holdout-archive
commit=feat: retain independent holdout archive
```

## Files

```text
docs/experiments/v5-kaggle-candidate-calibrator-independent-holdout-retention.md
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/archive_retention_report.json
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/environment_report.json
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/expected_outcome_records.jsonl
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/retention_manifest.json
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/runtime_records.jsonl
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/specsafe_v5_qwen_candidate_calibrator_holdout_attempt_001_t4.zip
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/timing_records.jsonl
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/trace_summary.json
tests/test_independent_holdout_archive_retention.py
```

## Boundary

This slice retains the independent holdout archive only.

It does not replay the candidate calibrator, tune thresholds, tune scheduler
policy, promote the calibrator, or authorize public final proof packaging.
