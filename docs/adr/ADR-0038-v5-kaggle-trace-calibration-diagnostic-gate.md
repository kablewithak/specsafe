# ADR-0038: V5 Kaggle Trace Calibration Diagnostic Gate

## Status
Accepted

## Context

PR #102 retained the first governed Kaggle trace archive. PR #103 added local trace diagnostics. PR #104 added a threshold replay gate and showed that raw draft probability is a useful diagnostic signal in the retained 24-record sample.

The next question is whether to fit or retain a calibration model over the Kaggle traces. The retained trace set is intentionally small: 24 candidate positions, 15 matches, and 9 non-matches. That is enough for a diagnostic calibration review, but not enough for a retained calibration fit.

## Decision

Add a deterministic calibration diagnostic gate over the retained archive.

The gate:

- uses `raw_draft_probability` as the runtime signal;
- uses `target_argmax_matches_candidate` as the post-hoc diagnostic label;
- computes Brier score and fixed-bin calibration diagnostics;
- records whether the sample is large enough for calibration fitting;
- blocks retained calibration fitting when sample support is insufficient;
- authorizes trace-corpus expansion before calibration fitting.

## Rationale

The retained traces show useful separation, but calibration fitting needs enough positive and negative examples to avoid turning a small-sample artifact into a pseudo-calibrator.

A diagnostic calibration report is useful now because it describes the shape of the signal without pretending the dataset is fit-ready.

## Consequences

The project gains a concrete calibration readiness boundary. The current trace archive is directionally supportive, but calibration fitting remains blocked until a larger governed trace corpus is collected.

This ADR does not authorize threshold selection, calibration model retention, policy promotion, public dataset release, throughput claims, latency claims, or production readiness.
