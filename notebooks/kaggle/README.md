# Kaggle Notebook Area

## Current notebook

`specsafe_v5_qwen_preflight.ipynb` is the first authorised Kaggle artifact.

It performs qualification only:

- resolve immutable Hugging Face revisions for the provisional Qwen pair;
- record restricted reproducibility metadata;
- reject a GPU architecture unsupported by the installed PyTorch CUDA build;
- prove exact tokenizer compatibility;
- prove finite logits access for each model;
- emit `specsafe_v5_qwen_preflight_result.json` in Kaggle working storage.

It does **not** collect traces, benchmark serving, publish a dataset, or make a runtime claim.

## Accelerator requirement

Use **GPU T4 x2** with Internet enabled. The first retained attempt on a Tesla P100 was blocked because its `sm_60` architecture was unsupported by the installed Kaggle PyTorch CUDA build.

## Retained first attempt

```text
evidence/kaggle-preflight/v5-qwen-same-tokenizer-preflight-v1/attempt-001-p100-result.json
```

Read before running:

```text
docs/adr/ADR-0029-v5-kaggle-model-pair-selection-and-preflight.md
docs/adr/ADR-0030-v5-kaggle-preflight-notebook-qualification.md
docs/adr/ADR-0031-v5-kaggle-preflight-compatibility-remediation.md
docs/experiments/v5-kaggle-same-tokenizer-trace-acquisition-charter.md
docs/experiments/v5-kaggle-qwen-preflight-runbook.md
```

Before its run, update only the `SOURCE_COMMIT_SHA` configuration value with the exact merged `main` commit SHA.
