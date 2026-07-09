# V5 Kaggle Negative-Case Expansion Plan

## Purpose

This plan defines the next governed evidence boundary after the `v5-qwen-governed-trace-collection-v2 / attempt-001-t4` calibration diagnostic.

The v2 diagnostic result is directionally supportive, but calibration fitting remains blocked because the negative count is below the declared minimum:

```text
observed_record_count=120
observed_positive_count=97
observed_negative_count=23
minimum_record_count_for_calibration_fit=100
minimum_positive_count_for_calibration_fit=30
minimum_negative_count_for_calibration_fit=30
calibration_fit_authorized=false
readiness_status=insufficient_negative_count_for_calibration_fit_signal_supportive
```

The goal of this plan is to govern a targeted negative-case expansion that increases nonmatch coverage without fitting calibration, promoting thresholds, or weakening the diagnostic gate.

## Current evidence state

```text
latest_retained_archive=v5-qwen-governed-trace-collection-v2 / attempt-001-t4
runtime_records=120
expected_outcome_records=120
case_count=30
target_argmax_matches=97
target_argmax_nonmatches=23
raw_confidence_roc_auc_diagnostic=0.8655311519497983
calibration_fit_authorized=false
```

Interpretation:

- The confidence signal is directionally useful.
- Threshold replay is directionally supportive.
- Calibration fitting is still not authorized.
- The next blocker is negative-class coverage, not total record count.

## Planned expansion identity

```text
collection_id=v5-qwen-governed-negative-case-expansion-v1
attempt_id=attempt-001-t4
data_role=trace_collection
intended_evidence_class=kaggle_environment_measured
model_pair_id=qwen2.5-0.5b-draft-qwen2.5-1.5b-target
planned_runtime_records=64
planned_prompt_count=16
planned_candidate_positions_per_prompt=4
```

## Corpus design

The expansion corpus should intentionally stress likely divergence conditions while remaining self-authored and public-safe.

Planned prompt families:

1. `ambiguous_instruction_continuation`
2. `open_ended_reasoning_turn`
3. `code_like_syntax_edge_case`
4. `rare_token_or_format_switch`
5. `multi_constraint_completion`
6. `high_entropy_style_shift`
7. `counterfactual_short_answer`
8. `structured_but_underconstrained_output`

Each family should contain two prompts for a total of 16 prompts.

Each prompt should define four planned candidate positions. The prompt text may be retained only if it is self-authored, short, non-sensitive, and public-safe. If public publication risk is unclear, retain prompt hashes and safe summaries rather than raw text.

## Split policy

Use prompt-family-level split discipline:

```text
calibration_candidate=8 prompts / 32 records
final_evaluation_candidate=8 prompts / 32 records
```

The exact split names may be finalized in the corpus fixture, but related prompt variants must not cross split boundaries.

## Negative-case target

```text
minimum_additional_negative_target=12
minimum_combined_negative_target=30
```

This is a planning target, not an outcome guarantee. If the model pair still produces fewer than the required additional negatives, the result must be retained as evidence and calibration fitting must remain blocked.

## Required files in the next implementation slice

```text
data/fixtures/kaggle_negative_case_expansion_v1/prompt_corpus.json
data/fixtures/kaggle_negative_case_expansion_v1/manifest.json
data/fixtures/kaggle_negative_case_expansion_v1/authoring_ledger.md
tests/test_kaggle_negative_case_expansion_v1.py
```

Possible later pre-collection files:

```text
evidence/kaggle-trace-collection/v5-qwen-governed-negative-case-expansion-v1/pre-collection/pre_collection_manifest.json
scripts/prepare_kaggle_negative_case_expansion_precollection_manifest.py
```

## Acceptance criteria for corpus fixture slice

The corpus fixture slice should prove:

- 16 prompts exist.
- Each prompt has exactly four planned candidate positions.
- Planned runtime records equal 64.
- Prompt families are isolated by split.
- Workload types are balanced enough for diagnostic reporting.
- No private, secret, customer, or PII markers appear.
- No outcome labels are present before model execution.
- Calibration fit status remains `not_authorized`.
- Threshold promotion status remains `not_authorized`.

## What this plan does not authorize

This plan does not authorize:

- fitting a Kaggle-derived calibrator;
- changing the declared minimum negative count;
- choosing a threshold from v2 replay;
- promoting a scheduler;
- publishing Hugging Face artifacts;
- claiming production speedup, latency, throughput, cost savings, or production readiness.

## Next safe gate

After this plan merges, the next safe gate is the negative-case expansion corpus fixture with tests.
