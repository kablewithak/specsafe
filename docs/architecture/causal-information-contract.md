# Causal Information Contract

## Purpose

A SpecSafe policy must decide whether to admit the next block position for verification using
only information available before that position is sampled or verified.

## Approved runtime flow

```text
versioned trace metadata
  -> visible prefix before position k
  -> pre-sample conditional survival confidence for position k
  -> capacity snapshot
  -> CausalSchedulerContext
  -> policy decision
```

## Runtime fields allowed at position k

| Field | Why it is allowed |
|---|---|
| `trace_id`, `request_id` | Stable identity for traceability, not outcome evidence. |
| `workload_type`, `decode_round` | Request metadata available before the decision. |
| `visible_prefix_token_ids` | Tokens lawfully visible before position `k`. |
| `conditional_survival_confidence` | A pre-sample estimate for the current position. |
| `capacity_snapshot` | Current scheduling resource state. |

## Forbidden runtime information

| Forbidden category | Why it invalidates a runtime decision |
|---|---|
| Future sampled candidate tokens | It lets the decision depend on a token that is not yet available. |
| Target acceptance or rejection outcomes | It leaks the answer the verification step is meant to determine. |
| Observed evaluation labels | They belong to post-hoc scoring, not runtime control. |
| Retrospective optimal prefixes | They are oracle information, not deployable policy input. |
| Future-derived confidence | It carries continuation information unavailable at the earlier decision point. |

## Enforcement

- `CausalSchedulerContext` is immutable and forbids unknown fields.
- Its prefix length must match the current block position.
- `require_causal_runtime_context` accepts only the exact approved contract type.
- Test-only retrospective contexts must fail with
  `forbidden_future_information_access`.

## Boundary note

This contract is a project-level causal control. It does not, by itself, establish the full
losslessness conditions of a production speculative-decoding implementation.
