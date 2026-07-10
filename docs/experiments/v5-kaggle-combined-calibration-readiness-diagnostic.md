# V5 Kaggle Combined Calibration-Readiness Diagnostic

## Status

Diagnostic complete. Calibration fitting is authorized only as the next separate gate.

## Inputs

This report combines two retained Kaggle archives:

- `v5-qwen-governed-trace-collection-v2 / attempt-001-t4`
- `v5-qwen-negative-case-expansion-v1 / attempt-001-t4`

The combined pool uses retained runtime and expected-outcome records. It does not rerun Kaggle,
reload models, regenerate labels, tune thresholds, or fit calibration.

## Combined counts

- Combined records: 184
- Combined matches: 148
- Combined nonmatches: 36
- Minimum records required for calibration fit: 100
- Minimum positives required for calibration fit: 30
- Minimum negatives required for calibration fit: 30

The previous negative-count blocker is resolved on raw count.

## Diagnostic metrics

- Raw confidence ROC-AUC diagnostic: `0.8363363363363363`
- Brier diagnostic: `0.2315717785677341`
- Fixed-bin ECE diagnostic: `0.303107947009899`
- Fixed-bin MCE diagnostic: `0.430998647990434`

The ranking signal is directionally supportive. Raw confidence is still visibly
miscalibrated, which is expected before fitting. This diagnostic authorizes only the next
calibrator-fitting gate, not calibrator promotion.

## Readiness decision

`sample_and_signal_ready_for_calibration_fit`

`calibration_fit_authorized=true`

This means a separate PR may fit a Kaggle-derived calibrator under an explicit split and
holdout boundary.

## Proposed next fit boundary

Candidate fitting splits:

- `v2_trace_collection:calibration`
- `negative_case_expansion:negative_probe_calibration_candidate`

Holdout or final-evaluation splits:

- `v2_trace_collection:final_evaluation`
- `v2_trace_collection:adversarial_regression`
- `negative_case_expansion:negative_probe_holdout`

## Evidence boundary

This is deterministic local combined diagnostic only.

It does not:

- rerun Kaggle model inference
- fit a Kaggle-derived calibrator
- promote a calibrator
- tune or promote thresholds
- promote scheduler utility
- publish public artifacts
- claim production speedup, latency, throughput, cost savings, or production readiness

## Next safe gate

Fit a Kaggle-derived calibrator under a separate gated PR.

The fitting PR must retain the fitted artifact, fixed split policy, before/after metrics,
holdout diagnostics, non-claim markers, and regression tests. Threshold promotion and
scheduler promotion remain blocked after this diagnostic.
