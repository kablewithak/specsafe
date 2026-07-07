# ADR-0027: Retain One Governed Controlled Synthetic Policy-Comparison Result

## Status

Accepted.

## Context

SpecSafe now has a frozen six-case synthetic matched-comparison corpus, strict valid
baselines, a guarded calibrated causal load-aware policy, a shared synthetic utility scorer,
and a case-level comparison harness. The next evidence need is execution discipline: the
corpus must be run under one fixed protocol and the resulting case-level evidence must be
retained without silently rerunning, selecting only favorable cases, refitting calibration,
or promoting a global policy winner.

The retained V5 calibration assessment authorizes controlled policy research only. It does
not authorize final-evaluation tuning, runtime control, production claims, or a global
policy recommendation.

## Decision

Add a governed write-once execution boundary with the following fixed inputs:

- `synthetic-matched-policy-comparison-v1` fixture manifest;
- `synthetic-capacity-profiles-v1` manifest;
- retained V5 bounded monotone-beta calibration artifact;
- retained passing V5 calibration-eligibility assessment;
- fixed baseline, threshold, adaptive, unsafe-control, comparison, and scorer configurations.

The runner shall retain a single canonical result at:

```text
evidence/matched-policy-comparison/v5-controlled-synthetic-comparison-v1/result.json
```

The retained result shall include all six cases, the invalid unsafe-control exclusion for
every case, all valid case-level outcomes, and aggregate counts only. It shall not include a
global winner, promotion decision, runtime-control status, throughput claim, latency claim,
cost-saving claim, or production claim.

## Consequences

### Enables

- reproducible controlled execution against immutable synthetic inputs;
- visible retention of neutral, losing, and higher-utility case outcomes;
- a stable machine-readable input for the next reporting gate;
- a deterministic integrity check over current contracts and frozen dependencies.

### Does not enable

- final held-out policy evaluation;
- calibration refit or threshold tuning;
- runtime control;
- a production, latency, cost, capacity, or serving claim;
- public summary reporting or policy promotion.

## Failure posture

Execution rejects:

- fixture or capacity-manifest hash drift;
- retained calibration-artifact hash drift;
- non-passing or altered V5 eligibility evidence;
- corpus case-order drift;
- profile mismatch;
- output overwrite;
- destinations outside the project root.

## Follow-on boundary

The next slice may generate a human-readable controlled-comparison report from this retained
machine-readable result. That report must preserve all valid, neutral, losing, and unsafe
outcomes and must keep claims limited to controlled synthetic evidence.
