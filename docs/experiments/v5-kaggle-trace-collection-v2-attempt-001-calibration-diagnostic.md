# V5 Kaggle Trace Collection V2 Attempt 001 — Calibration Diagnostic

## Status

```text
status=calibration_readiness_diagnostic_only
collection_id=v5-qwen-governed-trace-collection-v2
attempt_id=attempt-001-t4
```

This diagnostic reads the retained local archive only. It does not rerun Kaggle model inference, fit a calibrator, tune thresholds, promote a scheduler, publish public artifacts, or make production claims.

## Inputs

```text
runtime_records.jsonl
expected_outcome_records.jsonl
timing_records.jsonl
trace_summary.json
environment_report.json
retention_manifest.json
trace_analysis_report.json
trace_replay_report.json
```

## Diagnostic findings

```text
runtime_record_count=120
expected_outcome_record_count=120
joined_record_count=120
case_count=30
target_argmax_match_count=97
target_argmax_nonmatch_count=23
raw_confidence_roc_auc_diagnostic=0.8655311519497983
raw_draft_probability_brier_diagnostic=0.18776377614415718
fixed_bin_expected_calibration_error=0.2469890072320898
fixed_bin_maximum_calibration_error=0.44021765887737274
signal_diagnostic_passed=true
```

The confidence ranking signal is directionally supportive. Matches tend to receive higher draft confidence than nonmatches, and the replay frontier remains clean above the diagnostic threshold observed in the prior replay report.

## Calibration-fit readiness

```text
minimum_record_count_for_calibration_fit=100
minimum_positive_count_for_calibration_fit=30
minimum_negative_count_for_calibration_fit=30
observed_record_count=120
observed_positive_count=97
observed_negative_count=23
calibration_fit_readiness_status=insufficient_negative_count_for_calibration_fit_signal_supportive
calibration_fit_authorized=false
calibration_fit_status=not_authorized_by_diagnostic
next_authorized_step=expand_negative_case_coverage_before_calibration_fit
```

The v2 archive passes the total-record and positive-count minimums, but it does not pass the minimum negative-count gate. The result is promising, but it is not enough to fit or retain a Kaggle-derived calibrator under the current gate.

## Evidence boundary

This report supports the claim that the expanded v2 Kaggle archive has a useful confidence-ranking signal under the retained experimental conditions.

It does not support:

- Kaggle-derived calibrator fitting
- threshold promotion
- scheduler promotion
- public release
- production speedup, latency, throughput, cost savings, or production readiness

## Next safe gate

The next safe slice is governance for negative-case expansion or a targeted high-entropy third collection plan. The goal is to increase negative/nonmatch coverage before any calibration-fit decision.
