# Kaggle Notebook Area

## Current notebook

`specsafe_v5_qwen_preflight.ipynb` is the first authorised Kaggle artifact.

It performs qualification only:

- resolve immutable Hugging Face revisions for the provisional Qwen pair;
- record restricted reproducibility metadata;
- prove exact tokenizer compatibility;
- prove finite logits access for each model;
- emit `specsafe_v5_qwen_preflight_result.json` in Kaggle working storage.

It does **not** collect traces, benchmark serving, publish a dataset, or make a runtime claim.

Read before running:

```text
docs/adr/ADR-0029-v5-kaggle-model-pair-selection-and-preflight.md
docs/adr/ADR-0030-v5-kaggle-preflight-notebook-qualification.md
docs/experiments/v5-kaggle-same-tokenizer-trace-acquisition-charter.md
docs/experiments/v5-kaggle-qwen-preflight-runbook.md
```

The notebook must run in Kaggle with Internet and a GPU enabled. Before its run, update only the `SOURCE_COMMIT_SHA` configuration value with the exact merged `main` commit SHA.
