# V5 Kaggle Governed Trace Collection Attempt 001 Report

## Summary

Attempt 001 produced and retained the first real-model SpecSafe trace archive from Kaggle.
The separate terminal result JSON was not retained after a Kaggle browser/session refresh removed `/kaggle/working` outputs, so this report treats the archive and its manifest as the authoritative retained payload.

```text
collection_id=v5-qwen-governed-trace-collection-v1
collection_attempt_id=attempt-001-t4
source_commit_sha=cff5905075044770010653c637d3c52c4ccb6fbe
preflight_attempt_id=attempt-003-t4-pass
archive_sha256=03059b5ed15fdde07faff92cb9485cb89793e03e010fd8f43b8f674d17fdb81c
```

## Retained files

```text
specsafe_v5_qwen_trace_collection_v1_attempt_001.zip
retention_manifest.json
trace_summary.json
```

The retained archive contains:

```text
runtime_records.jsonl        sha256=19f9b35ad6d5bec552a92e835cdf92ee1cabfff26f4e502722389402e9f216b9
expected_outcomes.jsonl      sha256=f42cb4222dbdfe27af4b5ca10dc9b59ba705b559c14362c019f707c6edee8060
manifest.json                sha256=550f6a370ecd8a914738634cef7c9d5e3af48867bb8c92c19d60202a82024a62
```

## Provenance

```text
draft_model=Qwen/Qwen2.5-0.5B@060db6499f32faf8b98477b0a26969ef7d8b9987
target_model=Qwen/Qwen2.5-1.5B@8faed761d45a263340a0528343f099c05c9a4323
tokenizer_source_model=Qwen/Qwen2.5-0.5B@060db6499f32faf8b98477b0a26969ef7d8b9987
gpu=Tesla T4
gpu_architecture=sm_75
seed=20260708
decoding_configuration_id=greedy-next-token-block-4-v1
```

## Record counts

```text
case_count=6
runtime_record_count=24
expected_outcome_record_count=24
```

## First measured signal

Across the 24 candidate positions, the target model's greedy next token matched the draft candidate 15 times.

```text
target_argmax_match_count=15
target_argmax_nonmatch_count=9
target_argmax_match_rate=0.625
```

By block position:

```text
position_1=2/6 matched
position_2=4/6 matched
position_3=5/6 matched
position_4=4/6 matched
```

By workload type:

```text
code=7/8 matched
structured_text=5/8 matched
open_ended_chat=3/8 matched
```

Draft probability separated matched from non-matched candidates in this small trace archive:

```text
mean_raw_draft_probability_when_matched=0.703372
mean_raw_draft_probability_when_not_matched=0.248530
mean_raw_draft_entropy_when_matched=1.389121
mean_raw_draft_entropy_when_not_matched=3.863036
```

Threshold sensitivity over the raw draft probability is recorded in `trace_summary.json` for diagnostic use only.
It is not yet a calibrated threshold, a utility result, or a promotion gate.

## Evidence gap

The Kaggle terminal result JSON was not retained.
The final screenshot in the working session showed:

```text
status=passes_governed_trace_collection
failure_code=null
archive_created=true
trace_collection_performed=true
```

The repository does not recreate that missing JSON.
The absence is documented in `retention_manifest.json`.

## Interpretation boundary

This attempt supports local analysis of real-model trace behavior.
It does not prove calibration fitness, policy utility, speculative decoding losslessness, production throughput, latency, cost savings, public dataset readiness, or production readiness.

## Next authorized step

The next repository slice may build a local archive-analysis harness that ingests this retained archive, validates schemas and hashes, and computes controlled diagnostic summaries.
Calibration refit and policy comparison remain later gates.
