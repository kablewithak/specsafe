# V5 Kaggle Candidate Calibrator Independent Holdout Analysis

## Status

Complete. This slice analyzes the retained independent holdout archive and confirms whether it is structurally ready for a separate no-refit candidate-calibrator replay.

## Boundary

This is archive analysis only. It does not load, refit, replay, or promote the candidate calibrator. It does not select thresholds or execute scheduler policy logic.

## Inputs

The analysis uses the retained files under:

```text
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/
```

It joins runtime and expected-outcome records on:

```text
(trace_id, decode_round, block_position_index)
```

Timing coverage is checked by `trace_id`.

## Result

```text
analysis_status=replay_ready
runtime_records=192
expected_outcome_records=192
timing_records=192
joined_records=192
unique_traces=192
cases=48
duplicate_join_keys=0
missing_runtime_outcomes=0
missing_runtime_timings=0
```

Coverage remains balanced by retained workload size:

```text
code=64 records; 55 positive; 9 negative
open_ended_chat=64 records; 45 positive; 19 negative
structured_text=64 records; 36 positive; 28 negative
```

Position coverage is complete at 48 records per block position. Position 1 contains 26 negative outcomes, while positions 2 through 4 retain 13, 7, and 10 negatives respectively.

Raw-confidence diagnostics are retained only as archive characterization:

```text
raw_brier_diagnostic=0.18747805218884495
raw_discrimination_auc=0.881827731092437
```

These values are not candidate-calibrator holdout results.

## Replay field map

The next no-refit replay slice can consume:

```text
calibrator input=runtime_records.raw_confidence
diagnostic label=expected_outcome_records.observed_acceptance
workload stratum=workload_type
position stratum=block_position_index
```

Required provenance is available through collection, attempt, trace schema, model pair, model revisions, tokenizer revision, and split fields.

## Promotion gate

```text
candidate_calibrator_promotion=not_authorized_pending_independent_holdout_replay
threshold_promotion=not_authorized
scheduler_promotion=not_authorized
```

The retained holdout archive must not be used to refit the candidate calibrator, tune thresholds, or tune scheduler policy logic.

## Next safe slice

Replay the already-retained candidate calibrator against these independent holdout records without refitting. Produce the governed holdout replay report required by ADR-0041, then make promotion a separate decision.
