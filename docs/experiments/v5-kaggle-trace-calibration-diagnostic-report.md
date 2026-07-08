# V5 Kaggle Trace Calibration Diagnostic Report

## Scope

This report summarizes a deterministic diagnostic calibration review over the first retained Kaggle trace archive.

The diagnostic uses:

- runtime signal: `raw_draft_probability`
- diagnostic label: `target_argmax_matches_candidate`
- retained archive: `specsafe_v5_qwen_trace_collection_v1_attempt_001.zip`
- retained analysis report: `trace_analysis_report.json`
- retained replay report: `trace_replay_report.json`

## Main calibration diagnostics

- runtime records: `24`
- target-argmax matches: `15`
- target-argmax non-matches: `9`
- Brier diagnostic: `0.13062574344890066`
- fixed-bin ECE diagnostic: `0.1131004597991705`
- fixed-bin maximum calibration error diagnostic: `0.2314736247062683`

## Fixed-bin observations

- raw probability `[0.0, 0.2)`: `4` records, `1` match, observed rate `0.25`
- raw probability `[0.2, 0.4)`: `5` records, `1` match, observed rate `0.2`
- raw probability `[0.4, 0.6)`: `6` records, `4` matches, observed rate `0.6666666666666666`
- raw probability `[0.6, 0.8)`: `1` record, `1` match, observed rate `1.0`
- raw probability `[0.8, 1.0]`: `8` records, `8` matches, observed rate `1.0`

## Readiness decision

The calibration signal is directionally supportive, but the sample is not fit-ready.

Retained readiness gate:

- minimum records required for calibration fit: `100`
- minimum positives required: `30`
- minimum negatives required: `30`
- observed records: `24`
- observed positives: `15`
- observed negatives: `9`
- readiness status: `insufficient_sample_for_calibration_fit_signal_supportive`
- next authorized step: `expand_trace_corpus_before_calibration_fit`

## Interpretation boundary

This is a retained-archive calibration diagnostic.

It does not fit calibration, retain a calibration model, select a threshold, evaluate promoted policy utility, measure throughput, measure latency, publish a dataset, release a replay demo, or establish production readiness.
