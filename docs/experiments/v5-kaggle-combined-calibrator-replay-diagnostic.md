# V5 Kaggle Combined Calibrator Replay Diagnostic

## Status

Candidate calibrator replay diagnostic retained.

This slice applies the retained candidate calibrator to the same combined v2 plus
negative-case fit pool and records deterministic replay diagnostics.

It is not a holdout evaluation. It does not promote the calibrator, thresholds,
scheduler utility, public artifacts, or production claims.

## Source evidence

- v2 records: 120
- v2 matches: 97
- v2 nonmatches: 23
- negative-case records: 64
- negative-case matches: 51
- negative-case nonmatches: 13
- combined records: 184
- combined matches: 148
- combined nonmatches: 36

## Candidate calibrator replay

- Model ID: `v5-qwen-combined-fixed-bin-isotonic-calibrator-v1`
- Replay status: `fit_pool_replay_passed`
- Holdout status: `not_available_fit_pool_replay_only`
- Calibrator promotion status: `not_authorized_no_holdout`

## Fit-pool replay diagnostics

These are fit-pool replay diagnostics only.

- Raw Brier diagnostic: `0.2315717785677341`
- Calibrated Brier fit-pool replay diagnostic: `0.11977357092886388`
- Fit-pool Brier delta: `0.1117982076388702`

## Calibrated threshold replay preview

- Calibrated threshold `0.5`: selected 184 records, 148 matches, 36 nonmatches
- Calibrated threshold `0.6`: selected 142 records, 126 matches, 16 nonmatches
- Calibrated threshold `0.7`: selected 97 records, 95 matches, 2 nonmatches
- Calibrated threshold `0.8`: selected 97 records, 95 matches, 2 nonmatches
- Calibrated threshold `0.9`: selected 74 records, 74 matches, 0 nonmatches
- Calibrated threshold `0.95`: selected 74 records, 74 matches, 0 nonmatches

The replay is directionally supportive, but because it is fit-pool replay rather
than independent holdout evidence, it does not authorize promotion.

## Retained artifact

- `evidence/kaggle-trace-calibration/v5-qwen-combined-v2-negative-case/calibrator_replay_report.json`

## Evidence boundary

This slice is deterministic candidate-calibrator replay only.

It does not:

- rerun Kaggle model inference
- refit the candidate calibrator
- promote the candidate calibrator
- tune or promote thresholds
- promote scheduler utility
- publish public artifacts
- claim production speedup, latency, throughput, cost savings, or production readiness

## Next safe gate

Make an explicit promotion/holdout governance decision before any calibrator promotion.
If promotion remains blocked by lack of independent holdout evidence, proceed with a
public-proof/evidence-inventory path that labels the calibrator as a retained candidate,
not a promoted production policy.
