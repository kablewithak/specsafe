# V5 Kaggle Qwen Preflight Runbook

## Scope

This runbook executes the repository notebook:

```text
notebooks/kaggle/specsafe_v5_qwen_preflight.ipynb
```

It qualifies a model pair. It does not collect traces.

## Retained failed attempts

Two failed qualification attempts are retained:

```text
evidence/kaggle-preflight/v5-qwen-same-tokenizer-preflight-v1/attempt-001-p100-result.json
evidence/kaggle-preflight/v5-qwen-same-tokenizer-preflight-v1/attempt-002-t4-result.json
```

Attempt 001 used a Tesla P100 (`sm_60`) unsupported by the Kaggle PyTorch build and exposed a legacy special-token API assumption.

Attempt 002 used a compatible Tesla T4 (`sm_75`) and passed exact tokenizer qualification. It stopped at a too-strict logits vocabulary equality rule. No traces were collected in either attempt.

## Before opening Kaggle

After this remediation pull request is merged, update local `main` and record its exact full commit SHA:

```powershell
git switch main
git pull --ff-only origin main
git rev-parse HEAD
```

Copy that full SHA. It will be placed in the notebook configuration cell as `SOURCE_COMMIT_SHA`.

## Kaggle setup

1. Create a **fresh Kaggle Python notebook** and upload the updated `specsafe_v5_qwen_preflight.ipynb`.
2. In Notebook Settings, enable **Internet** and select **GPU T4 x2**.
3. Replace only this notebook configuration value:

```python
SOURCE_COMMIT_SHA = "RECORD_MAIN_COMMIT_SHA_AFTER_PR_MERGE"
```

with the exact full SHA from the local command above.

4. Run every cell in order.

Do not add a Hugging Face token, Kaggle secret, customer data, private prompt, or private dataset.

## Expected output

The final cell writes:

```text
/kaggle/working/specsafe_v5_qwen_preflight_result.json
```

Download that JSON file whether the notebook passes or fails. Do not edit it after execution.

## Pass condition

```text
preflight_status=passes_kaggle_preflight
trace_collection_allowed=true
trace_collection_performed=false
```

A pass authorizes the next trace-collection design slice only.

## Failure condition

```text
preflight_status=fails_kaggle_preflight
trace_collection_allowed=false
```

Do not collect traces. Download the result file and provide it to the next SpecSafe session. Do not substitute a different model pair without a new ADR.

## Non-claims

This preflight does not establish model quality, trace quality, throughput, latency, cost savings, serving capacity, production readiness, or a public dataset.
