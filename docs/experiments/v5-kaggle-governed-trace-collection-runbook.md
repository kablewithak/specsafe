# V5 Governed Kaggle Qwen Trace-Collection Runbook

## Preconditions

- ADR-0033 is merged.
- The current notebook source commit SHA is recorded in the configuration cell.
- Use a **fresh** Kaggle notebook created from `notebooks/kaggle/specsafe_v5_qwen_trace_collection.ipynb`.
- Kaggle Settings: Internet **on**, Accelerator **GPU T4 x2**.
- Do not add secrets, an HF token, external datasets, private prompts, or user data.

## Immutable collection inputs

```text
collection_id=v5-qwen-governed-trace-collection-v1
collection_attempt_id=attempt-001-t4
preflight_attempt_id=attempt-003-t4-pass
preflight_result_sha256=4b2e096ecf57e7c729918a83a6b84434ab0dc9dac094f6b9eadff40f84e7d9dd
prompt_corpus_id=v5-qwen-self-authored-trace-corpus-v1
prompt_corpus_sha256=ffe698c9d9c41ea4a374ca7d12293130c832a7523f7554079314875afcce3d52
draft_model=Qwen/Qwen2.5-0.5B@060db6499f32faf8b98477b0a26969ef7d8b9987
target_model=Qwen/Qwen2.5-1.5B@8faed761d45a263340a0528343f099c05c9a4323
decoding_configuration_id=greedy-next-token-block-4-v1
max_block_positions=4
```

## What the notebook exports

```text
runtime_records.jsonl
expected_outcomes.jsonl
manifest.json
specsafe_v5_qwen_trace_collection_v1_attempt_001.zip
specsafe_v5_qwen_trace_collection_result_attempt_001.json
```

The runtime JSONL excludes target-derived outcomes. The expected-outcome JSONL excludes raw prompt text and includes only minimized labels and aggregate probability features.

## Stop rules

Stop immediately after the first terminal result.

- On failure: download the result JSON only. Do not rerun, modify prompts, change models, or consume partial output.
- On pass: download the result JSON and the ZIP archive. Do not publish or attach the archive to a public dataset.

## Next safe action after a pass

Upload the result JSON and archive here. The next repository slice validates the archive locally, retains it with a manifest, and assigns governed roles/splits before any calibration or policy work.
