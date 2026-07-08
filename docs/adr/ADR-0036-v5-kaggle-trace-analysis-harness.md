# ADR-0036: V5 Kaggle Trace Analysis Harness

## Status

Accepted.

## Context

PR #102 retained the first governed Kaggle trace-collection archive for `v5-qwen-governed-trace-collection-v1/attempt-001-t4`.

The retained archive contains 24 runtime records and 24 expected-outcome records over six self-authored prompts. The terminal result JSON was not retained because the Kaggle browser/session refresh removed `/kaggle/working` outputs before the separate JSON could be downloaded. The trace archive itself was retained and hash-addressed.

The next engineering step is local analysis of that retained archive. The analysis must be reproducible from the archive and must not quietly become a calibration fit, policy threshold selection, policy-utility comparison, benchmark, or public dataset release.

## Decision

Add a local trace-analysis harness under `specsafe.kaggle_trace_analysis`.

The harness:

- loads the retained Kaggle trace archive;
- validates the archive member set;
- validates the retained runtime, expected-outcome, and manifest records using the existing Kaggle trace-collection contracts;
- joins runtime records to post-hoc outcomes using `(trace_id, decode_round, block_position_index)`;
- rejects duplicate or missing join keys;
- computes deterministic diagnostics over the retained archive;
- writes a schema-versioned `trace_analysis_report.json`;
- preserves the interpretation boundary in machine-readable form.

The report computes:

- total candidate count;
- target-argmax match count and rate;
- matched and non-matched candidate statistics;
- workload, case, and block-position strata;
- raw draft probability threshold sensitivity;
- pairwise draft-probability separation;
- pairwise entropy separation;
- a diagnostic Brier-style score over raw draft probability versus target-argmax match labels.

The threshold sweep is explicitly diagnostic only. It does not select a policy threshold.

## Evidence retained

The local analysis report is retained at:

```text
/evidence/kaggle-trace-collection/v5-qwen-governed-trace-collection-v1/attempt-001-t4/trace_analysis_report.json
```

Report SHA-256:

```text
90915a600bc481fa451ef07366cb2a8b8dba7b89e1cb16375f64896c03f9552d
```

The retained report is reproducible from:

```text
/evidence/kaggle-trace-collection/v5-qwen-governed-trace-collection-v1/attempt-001-t4/specsafe_v5_qwen_trace_collection_v1_attempt_001.zip
```

Archive SHA-256:

```text
03059b5ed15fdde07faff92cb9485cb89793e03e010fd8f43b8f674d17fdb81c
```

## Consequences

The project now has a local, deterministic analysis boundary for the first real-model trace archive.

The results are directionally supportive: raw draft probability and entropy separate matched from non-matched candidates in this small sample. They are not yet calibration, replay, or policy-utility findings.

A later slice may use this analysis report to decide whether to build a calibration/replay harness over the retained Kaggle traces. That later step must remain gated separately.

## Non-decisions

This ADR does not authorize:

- calibration refit;
- policy threshold selection;
- policy-utility comparison;
- throughput or latency claims;
- public dataset release;
- replay demo release;
- production readiness claims.
