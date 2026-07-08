# Kaggle Notebook Area

## Current notebook

`specsafe_v5_qwen_preflight.ipynb` is the completed model-pair qualification notebook.

It performs qualification only:

- resolves immutable Hugging Face revisions for the approved Qwen pair;
- records restricted reproducibility metadata;
- rejects unsupported GPU architectures before model-hub activity;
- proves exact tokenizer compatibility;
- proves finite logits access while allowing a model output vocabulary padded beyond tokenizer length;
- emits `specsafe_v5_qwen_preflight_result.json` in Kaggle working storage.

It does **not** collect traces, benchmark serving, publish a dataset, or make a runtime claim.

## Retained preflight attempts

```text
evidence/kaggle-preflight/v5-qwen-same-tokenizer-preflight-v1/attempt-001-p100-result.json
evidence/kaggle-preflight/v5-qwen-same-tokenizer-preflight-v1/attempt-002-t4-result.json
evidence/kaggle-preflight/v5-qwen-same-tokenizer-preflight-v1/attempt-003-t4-pass-result.json
evidence/kaggle-preflight/v5-qwen-same-tokenizer-preflight-v1/preflight_attempt_registry.json
```

Attempt 003 passed on GPU T4 x2 with Internet enabled. It authorizes the implementation of the next governed trace-collection notebook, not ad hoc trace collection or publication.

## Accelerator requirement

Use **GPU T4 x2** with Internet enabled for any future Qwen notebook run unless a later ADR changes the approved environment.

## Read before future Kaggle work

```text
docs/adr/ADR-0029-v5-kaggle-model-pair-selection-and-preflight.md
docs/adr/ADR-0030-v5-kaggle-preflight-notebook-qualification.md
docs/adr/ADR-0031-v5-kaggle-preflight-compatibility-remediation.md
docs/adr/ADR-0032-v5-kaggle-qwen-logits-preflight-remediation.md
docs/adr/ADR-0033-v5-kaggle-preflight-pass-and-trace-collection-authorization.md
docs/experiments/v5-kaggle-qwen-preflight-runbook.md
docs/experiments/v5-kaggle-governed-trace-collection-readiness.md
```
