# V5 Kaggle Candidate Calibrator Independent Holdout Archive Retention

## Status

```text
retention_status=retained
collection_id=v5-qwen-candidate-calibrator-independent-holdout-v1
attempt_id=attempt-001-t4
data_role=independent_holdout_trace_collection
evidence_class=kaggle_environment_measured
```

## Purpose

This document records retention of the independent holdout archive collected for
the retained combined Kaggle candidate calibrator.

This retention step preserves the holdout evidence exactly enough for later
analysis and calibrator replay. It does not authorize promotion.

## Retained artifacts

```text
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/specsafe_v5_qwen_candidate_calibrator_holdout_attempt_001_t4.zip
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/archive_retention_report.json
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/environment_report.json
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/expected_outcome_records.jsonl
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/retention_manifest.json
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/runtime_records.jsonl
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/timing_records.jsonl
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/trace_summary.json
```

## Retention facts

```text
archive_sha256=3ab63ecd516be39ead9901ccc99d1d7a90f09bb2dcde5ca01bd5e258dfa03279
archive_byte_count=31800
case_count=48
runtime_record_count=192
expected_outcome_record_count=192
timing_record_count=192
target_argmax_match_count=136
target_argmax_nonmatch_count=56
target_argmax_match_rate=0.7083333333333334
raw_prompt_text_retained=false
```

## Workload coverage

```text
code=64
open_ended_chat=64
structured_text=64
```

## Environment facts

```text
python=3.12.13
torch=2.10.0+cu128
transformers=5.0.0
cuda_available=true
cuda_device_count=2
cuda_device_0=Tesla T4
cuda_device_1=Tesla T4
```

## Model boundary

```text
draft_model_id=Qwen/Qwen2.5-0.5B
draft_model_revision=060db6499f32faf8b98477b0a26969ef7d8b9987
target_model_id=Qwen/Qwen2.5-1.5B
target_model_revision=8faed761d45a263340a0528343f099c05c9a4323
tokenizer_id=Qwen/Qwen2.5-1.5B
tokenizer_revision=8faed761d45a263340a0528343f099c05c9a4323
```

## Current authorization boundary

```text
calibration_fit_status=not_authorized
calibrator_promotion_status=not_authorized_pending_independent_holdout_replay
threshold_promotion_status=not_authorized
scheduler_promotion_status=not_authorized
production_claim_status=not_authorized
```

## What this retention proves

```text
- The independent holdout archive was produced in Kaggle.
- The retained archive contains 48 holdout cases and 192 runtime records.
- Matching expected-outcome records and timing records are present.
- Raw prompt text is not retained in the trace records.
- The holdout archive contains enough nonmatches for a meaningful replay diagnostic.
```

## What this retention does not prove

```text
- calibrator holdout performance
- calibrator promotion readiness
- threshold promotion readiness
- scheduler promotion readiness
- adaptive-policy utility improvement
- Hugging Face final public proof readiness
- production speed, latency, throughput, cost, or serving readiness
```

## Next safe action

Analyze the retained holdout archive and then replay the already-retained
candidate calibrator against it without refitting or threshold tuning.
