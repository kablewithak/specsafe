# V5 Kaggle Combined Calibrator Fit — Candidate Retention

## Status

Candidate calibrator fit retained.

This slice fits a deterministic Kaggle-derived candidate calibrator after the combined
v2 plus negative-case calibration-readiness diagnostic authorized a fitting attempt.

It does not promote the calibrator, thresholds, scheduler utility, public artifacts, or
production claims.

## Source evidence

- v2 archive records: 120
- v2 matches: 97
- v2 nonmatches: 23
- negative-case archive records: 64
- negative-case matches: 51
- negative-case nonmatches: 13
- combined records: 184
- combined matches: 148
- combined nonmatches: 36

## Fitted candidate calibrator

- Model ID: `v5-qwen-combined-fixed-bin-isotonic-calibrator-v1`
- Calibrator type: `fixed_bin_laplace_isotonic_v1`
- Input feature: `raw_confidence`
- Output feature: `calibrated_acceptance_probability`
- Fit status: `fit_retained`
- Promotion status: `not_authorized`

The model uses fixed raw-confidence bins with Laplace smoothing and a simple
pool-adjacent-violators monotonicity pass. The non-monotonic `[0.2, 0.3)` and
`[0.3, 0.4)` bins were pooled into one `[0.2, 0.4)` block.

## In-sample diagnostic summary

These values are in-sample diagnostics over the fit pool. They are useful for checking
that the retained candidate is mechanically coherent, but they are not promotion evidence.

- Raw Brier diagnostic: `0.23157177856773398`
- Calibrated Brier in-sample diagnostic: `0.11977357092886376`
- In-sample Brier delta: `0.11179820763887022`
- Raw fixed-bin ECE diagnostic: `0.30310794700989907`
- Calibrated fixed-bin ECE in-sample diagnostic: `0.052728144595367316`
- In-sample ECE delta: `0.2503798024145317`
- Raw fixed-bin MCE diagnostic: `0.570609964106394`
- Calibrated fixed-bin MCE in-sample diagnostic: `0.14523589269195192`

## Retained artifacts

- `evidence/kaggle-trace-calibration/v5-qwen-combined-v2-negative-case/calibrator_model.json`
- `evidence/kaggle-trace-calibration/v5-qwen-combined-v2-negative-case/calibrator_fit_report.json`

## Evidence boundary

This slice authorizes and retains a candidate calibrator fit only.

It does not:

- rerun Kaggle model inference
- promote the candidate calibrator
- tune or promote thresholds
- promote scheduler utility
- publish public artifacts
- claim production speedup, latency, throughput, cost savings, or production readiness

## Next safe gate

Run a deterministic candidate-calibrator replay/holdout diagnostic before any promotion
decision. Promotion remains blocked until that separate gate passes.
