# V5 Kaggle Trace Analysis — Attempt 001

## Purpose

This report summarizes the first local diagnostic analysis over the retained Kaggle trace archive:

```text
collection_id=v5-qwen-governed-trace-collection-v1
collection_attempt_id=attempt-001-t4
source_commit_sha=cff5905075044770010653c637d3c52c4ccb6fbe
preflight_attempt_id=attempt-003-t4-pass
```

The analysis is produced by `specsafe.kaggle_trace_analysis` from the retained archive. It is not a manual summary.

## Retained inputs

```text
archive_path=evidence/kaggle-trace-collection/v5-qwen-governed-trace-collection-v1/attempt-001-t4/specsafe_v5_qwen_trace_collection_v1_attempt_001.zip
archive_sha256=03059b5ed15fdde07faff92cb9485cb89793e03e010fd8f43b8f674d17fdb81c
```

The archive contains:

```text
runtime_records.jsonl
expected_outcomes.jsonl
manifest.json
```

The terminal result JSON is not retained. That absence is documented in the retention manifest from PR #102 and is not manually recreated here.

## Local analysis command

```powershell
python .\scripts\analyze_kaggle_trace_archive.py `
    --archive .\evidence\kaggle-trace-collection\v5-qwen-governed-trace-collection-v1\attempt-001-t4\specsafe_v5_qwen_trace_collection_v1_attempt_001.zip `
    --output .\evidence\kaggle-trace-collection\v5-qwen-governed-trace-collection-v1\attempt-001-t4\trace_analysis_report.json
```

Expected terminal shape:

```text
wrote trace analysis report collection_id=v5-qwen-governed-trace-collection-v1 attempt=attempt-001-t4 records=24 match_rate=0.625000
```

## Main result

```text
runtime_record_count=24
expected_outcome_record_count=24
target_argmax_match_count=15
target_argmax_nonmatch_count=9
target_argmax_match_rate=0.625
```

## Candidate signal diagnostics

Matched candidates:

```text
mean_raw_draft_probability=0.70337240199248
median_raw_draft_probability=0.8019253015518188
mean_raw_draft_entropy=1.3891208976507188
mean_target_probability=0.683448655406634
mean_target_entropy=1.548857851450642
```

Non-matched candidates:

```text
mean_raw_draft_probability=0.24853027860323587
median_raw_draft_probability=0.21381868422031403
mean_raw_draft_entropy=3.863035930527581
mean_target_probability=0.2409138921648264
mean_target_entropy=3.977086557282342
```

Pairwise diagnostics:

```text
raw_draft_probability_pairwise_separation_rate=0.9037037037037037
raw_draft_entropy_pairwise_lower_for_match_rate=0.9111111111111111
raw_draft_probability_brier_diagnostic=0.13062574344890066
```

Interpretation: in this small archive, higher draft probability and lower draft entropy are directionally associated with target-argmax candidate agreement.

## Workload stratification

```text
code:             7/8 matched, match_rate=0.875
structured_text:  5/8 matched, match_rate=0.625
open_ended_chat:  3/8 matched, match_rate=0.375
```

This is consistent with the expected shape: constrained/code-like continuations are easier for the draft and target model to agree on than open-ended chat continuations.

## Block-position stratification

```text
position 1: 2/6 matched, match_rate=0.3333333333333333
position 2: 4/6 matched, match_rate=0.6666666666666666
position 3: 5/6 matched, match_rate=0.8333333333333334
position 4: 4/6 matched, match_rate=0.6666666666666666
```

This is a small trace set. Do not infer a stable positional law from it.

## Threshold sensitivity

The report includes a raw draft-probability threshold sweep. It is diagnostic only.

```text
threshold=0.3 selected=16 match_rate=0.8125
threshold=0.5 selected=13 match_rate=0.9230769230769231
threshold=0.7 selected=9  match_rate=1.0
threshold=0.8 selected=8  match_rate=1.0
threshold=0.9 selected=5  match_rate=1.0
```

This is a useful signal check, not a selected operating policy.

## Boundary

The analysis report states:

```text
analysis_scope=local_retained_archive_diagnostics
calibration_fit_performed=false
policy_threshold_selected=false
policy_utility_evaluation_performed=false
throughput_or_latency_measurement_performed=false
public_dataset_release_authorized=false
production_readiness_claimed=false
```

## Current finding status

The first retained real-model trace archive is directionally supportive of the SpecSafe north star: draft-model uncertainty appears to carry useful information about when draft candidates are likely to agree with the target model.

This is not yet the final finding. The next gate is to decide whether to build a calibration/replay harness over retained trace records.
