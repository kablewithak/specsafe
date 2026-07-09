# V5 Kaggle Trace Collection V2 — Attempt 001 T4 Retention Note

## Status

This note retains the second governed Kaggle trace-collection archive for
`v5-qwen-governed-trace-collection-v2 / attempt-001-t4`.

## Retained archive

```text
archive_name=specsafe_v5_qwen_trace_collection_v2_attempt_001_t4.zip
archive_sha256=b8803ea500378a6b91af6b0a5206fc4359d9b3f8bf1888a01907ded6f11e0e7a
source_commit=0dfd5118a471adeec92a609d817d06d698f783a7
```

## Collection summary

```text
runtime_record_count=120
expected_outcome_record_count=120
case_count=30
target_argmax_match_count=97
target_argmax_nonmatch_count=23
target_argmax_match_rate=0.8083333333333333
```

## Evidence boundary

This is a retained trace-collection archive, not a calibration artifact and not a
policy-promotion artifact.

The archive explicitly preserves these boundaries:

```text
calibration_fit_status=not_authorized
threshold_promotion_status=not_authorized
scheduler_promotion_status=not_authorized
production_claim_status=not_authorized
raw_prompt_text_retained=false
```

## Next safe gate

After this retention slice is merged, the next safe slice is local deterministic
analysis over the retained archive. That analysis may summarize signal quality,
record counts, and split/workload coverage. It must not fit a Kaggle-derived
calibrator, promote thresholds, promote a scheduler, or claim production speedup.
