# V5 Kaggle Negative-Case Expansion Pre-Collection Bundle

## Purpose

This document records the governed pre-collection manifest and readiness bundle for `v5-qwen-negative-case-expansion-v1 / attempt-001-t4`.

The v2 Kaggle calibration diagnostic was directionally supportive but blocked calibration fitting because the retained archive had only 23 observed negatives against a minimum requirement of 30. This slice prepares a targeted negative-case collection input boundary before any third Kaggle run.

## Planned collection shape

```text
collection_id=v5-qwen-negative-case-expansion-v1
attempt_id=attempt-001-t4
source_corpus_id=kaggle_negative_case_expansion_v1
planned_prompt_count=16
planned_candidate_positions_per_prompt=4
planned_runtime_records=64
minimum_additional_negative_records_needed=7
```

## Evidence boundary

This is pre-collection readiness only.

It does not:

- run Kaggle model inference;
- collect a third archive;
- fit a Kaggle-derived calibrator;
- tune or promote thresholds;
- promote scheduler utility;
- publish public artifacts;
- claim production speedup, latency, throughput, cost savings, or production readiness.

## Required Kaggle controls

- Private input dataset.
- GPU T4 accelerator only when readiness checks pass.
- Internet enabled only for model download.
- No secret printing.
- No calibration fitting.
- No threshold promotion.
- No scheduler promotion.
- Output archive must retain runtime/outcome separation.

## Next safe gate

After this slice merges, the next safe step is a Kaggle upload/run bundle for the negative-case expansion attempt. Calibration fitting remains blocked until the third archive is collected, retained, analyzed, replayed, and diagnostically evaluated.
