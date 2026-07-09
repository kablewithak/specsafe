# V5 Kaggle Trace Collection V2 Attempt 001 — Local Analysis

## Boundary

This document records deterministic local analysis over the retained Kaggle trace archive:

```text
collection_id=v5-qwen-governed-trace-collection-v2
attempt_id=attempt-001-t4
archive_sha256=b8803ea500378a6b91af6b0a5206fc4359d9b3f8bf1888a01907ded6f11e0e7a
analysis_status=diagnostic_analysis_only
```

The analysis reads retained local artifacts only. It does not rerun Kaggle, reload models,
fit calibration, tune thresholds, promote a scheduler, or authorize production claims.

## Retained input summary

```text
runtime_record_count=120
expected_outcome_record_count=120
timing_record_count=120
case_count=30
target_argmax_match_count=97
target_argmax_nonmatch_count=23
target_argmax_match_rate=0.8083333333333333
```

## Main diagnostic finding

The signal is directionally supportive:

```text
mean_raw_confidence_matches=0.6399255032391892
mean_raw_confidence_nonmatches=0.22993675295425497
mean_draft_entropy_matches=1.8441315958487619
mean_draft_entropy_nonmatches=3.7787872190060825
raw_confidence_roc_auc_diagnostic=0.8655311519497983
```

Plain-English interpretation: matched positions generally had higher draft confidence and
lower draft entropy than nonmatched positions. That is useful signal for the next diagnostic
replay and calibration-readiness gate.

## Calibration diagnostics from fixed bins

```text
raw_confidence_brier_diagnostic=0.18776377614415718
fixed_bin_expected_calibration_error=0.2469890072320898
fixed_bin_maximum_calibration_error=0.44021765887737274
```

Fixed-bin counts:

| Bin | Records | Matches | Nonmatches | Observed match rate |
|---|---:|---:|---:|---:|
| [0.0, 0.2) | 24 | 13 | 11 | 0.5416666666666666 |
| [0.2, 0.4) | 23 | 12 | 11 | 0.5217391304347826 |
| [0.4, 0.6) | 16 | 15 | 1 | 0.9375 |
| [0.6, 0.8) | 17 | 17 | 0 | 1.0 |
| [0.8, 1.0] | 40 | 40 | 0 | 1.0 |

## Stratification

Split record counts:

```text
adversarial_regression=12
calibration=36
development=36
final_evaluation=36
```

Workload record counts:

```text
code=40
open_ended_chat=40
structured_text=40
```

## Evidence boundary

Claims supported after this slice:

- The retained v2 Kaggle archive can be locally analyzed deterministically.
- Runtime and expected-outcome records join one-to-one by `trace_id`.
- Runtime records do not contain outcome labels or target-derived outcome fields.
- The v2 archive shows directionally supportive confidence signal.

Claims not supported after this slice:

- A Kaggle-derived calibrator is fit or authorized.
- A threshold policy is promoted.
- A scheduler is promoted from Kaggle evidence.
- Public release is authorized.
- Production speedup, latency, throughput, cost savings, or readiness are proven.

## Next safe gate

Run deterministic diagnostic replay over the retained v2 archive. Calibration fitting remains
blocked until a separate calibration-readiness diagnostic explicitly authorizes it.
