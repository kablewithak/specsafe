# Deterministic Synthetic Policy Replay

## Purpose

This boundary replays one policy over one immutable, hash-verified synthetic trace case.
It records a typed decision first and joins the corresponding expected outcome only after
that decision exists.

It is intentionally narrower than a policy-comparison report. It does not fit calibration,
select thresholds, estimate production throughput, assign a policy winner, or claim
load-aware scheduling benefit.

## Runtime versus evaluation boundary

```text
SyntheticTraceFixtureSet
  -> select one SyntheticTraceReplayCase by case_id
  -> provide one CausalSchedulerContext to policy.decide(...)
  -> validate returned VerificationDecision
  -> attach expected outcome after the decision
  -> retain typed replay result
```

A valid policy receives only `CausalSchedulerContext`. It never receives:

- `SyntheticTraceReplayCase`;
- expected outcomes;
- candidate token IDs;
- observed acceptance labels;
- prefix-survival labels;
- retrospective contexts.

The replay harness reads labels after retaining a decision in order to compute
`accepted_admission_count` and `rejected_admission_count`. Those labels do not feed back
into later runtime decisions.

## Valid replay path

`run_valid_policy_replay(...)` accepts a `SyntheticTraceFixtureSet`, a case ID, a policy,
and a run ID.

For every processed position it verifies:

1. the source context is the exact approved causal runtime contract;
2. the policy returns the exact `VerificationDecision` contract;
3. the decision is marked `causal_safety_status=pass`;
4. trace ID, decode round, and block-position identity match the source context;
5. all decisions within the replay share one policy ID.

A `STOP` or `CONSERVATIVE_FALLBACK` decision is terminal. The harness does not call the
policy for later positions. It retains the terminal decision and marks later runtime
positions as unprocessed.

A valid result is labelled:

```text
validity_status=valid_comparison
causal_safety_status=pass
```

This status says only that the retained replay may be used in a later comparison that also
satisfies shared-input, split, calibration, capacity, scoring, and report requirements.
It does not itself establish an advantage.

## Unsafe retrospective negative control

`run_unsafe_retrospective_replay(...)` is isolated in
`specsafe.trace_replay.unsafe_controls`.

It intentionally builds a `RetrospectiveEvaluationContext` from the current and remaining
expected outcomes. This makes unavailable future evidence available to the control solely
to demonstrate why a superficially favorable policy output is invalid.

Its output is permanently labelled:

```text
validity_status=invalid_causal_comparison
causal_safety_status=fail
evaluation_only=true
```

Unsafe replay results are not accepted by the valid replay path and cannot support a
valid-policy or promotion claim.

## Retained evidence

Every replay result retains:

- run ID;
- fixture-set ID and version;
- fixture ID, case ID, trace ID, and governed split;
- policy ID;
- total, processed, and unprocessed position counts;
- each typed decision and its post-hoc expected outcome;
- admitted, accepted-admission, and rejected-admission counts;
- terminal decode-round and position identity where a terminal decision occurred;
- validity and causal-safety status.

## Current boundaries and non-claims

This implementation uses only local synthetic fixtures and deterministic tests.

It does not yet retain a policy-configuration hash, model execution data, measured capacity
profile, calibrated confidence artifact, utility formula, cross-policy report, or a policy
winner. Those become required evidence only when later phases introduce calibration,
capacity-aware intervention, and governed comparison reporting.
