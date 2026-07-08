# Kaggle Notebook Area

## Completed qualification notebook

`specsafe_v5_qwen_preflight.ipynb` qualified the pinned Qwen pair on Kaggle GPU T4 x2. The retained passing artifact is recorded in `evidence/kaggle-preflight/`.

## Current governed trace-collection notebook

`specsafe_v5_qwen_trace_collection.ipynb` is the next approved notebook.

It uses the retained preflight lineage and collects one bounded attempt from a fixed six-case self-authored corpus. It exports separate runtime-candidate and target-derived outcome JSONL files, a manifest, an archive, and a terminal result JSON.

It does not fit calibration, evaluate policy utility, benchmark throughput, publish data, or make a serving claim.

## Required Kaggle settings

```text
Internet: ON
Accelerator: GPU T4 x2
```

## Before executing

Read:

```text
docs/adr/ADR-0033-v5-kaggle-preflight-pass-and-trace-collection-authorization.md
docs/adr/ADR-0034-v5-kaggle-governed-trace-collection-notebook.md
docs/experiments/v5-kaggle-governed-trace-collection-runbook.md
```
