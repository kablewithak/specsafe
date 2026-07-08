# ADR-0037: V5 Kaggle Trace Replay Gate

## Status
Accepted

## Context

PR #102 retained the first governed Kaggle trace archive. PR #103 added deterministic local diagnostics over that archive and showed that raw draft probability separated target-argmax matches from non-matches in the small retained sample.

The next question is not whether to select a production threshold. The next question is whether the retained traces are strong enough to justify a later calibration/replay harness without overclaiming.

## Decision

Add a deterministic threshold-replay gate over the retained Kaggle trace archive.

The replay gate:

- uses only retained runtime records and expected outcomes;
- treats `raw_draft_probability` as the runtime signal;
- treats `target_argmax_matches_candidate` as the post-hoc diagnostic label;
- evaluates a fixed threshold grid from `0.0` through `0.9`;
- computes selected count, selected match rate, mismatch rate, match recall, and penalty-sensitive diagnostic utility proxies;
- records that no threshold is selected and no calibration is fitted.

## Rationale

The trace-analysis report showed a useful signal, but a scheduler-facing project needs to inspect the operational trade-off: higher confidence thresholds reduce mismatch risk but also reject candidates that would have matched.

This replay gate makes that trade-off explicit without promoting a policy.

## Evidence boundary

This ADR authorizes only a local diagnostic replay over the retained Kaggle archive. It does not authorize calibration refit, policy promotion, throughput claims, latency claims, public dataset release, replay-demo release, or production readiness.

## Consequences

The project now has a deterministic local gate between first-trace diagnostics and any calibration/replay work. Later calibration work must be a separate gate and must not treat this small 24-record archive as sufficient for broad claims.
