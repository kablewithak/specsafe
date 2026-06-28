# ADR-0002: Enforce an Explicit Causal Information Boundary for Runtime Policies

- **Status:** Accepted
- **Date:** 2026-06-28

## Context

SpecSafe evaluates whether verification budget can be allocated more intelligently than fixed
rules. That comparison is invalid if a scheduler observes information that was unavailable when
its decision had to be made.

The relevant failure mode is retrospective look-ahead: a policy appears to improve utility by
using sampled future candidate tokens, target verification outcomes, or an after-the-fact optimal
prefix when deciding whether to admit an earlier position. In speculative decoding, that can
violate non-anticipation and invalidate a losslessness claim. In this project, any analogous
runtime decision is treated as invalid even when reported utility improves.

## Decision

SpecSafe will expose exactly one approved runtime input model:
`CausalSchedulerContext`.

It contains only:

- immutable trace and request identifiers;
- workload type and decode-round metadata;
- the visible token prefix before the current decision;
- a pre-sample conditional survival confidence for the current block position;
- a capacity snapshot visible at decision time.

It deliberately excludes:

- current or future sampled candidate token values;
- target acceptance or rejection outcomes;
- observed labels;
- retrospective optimal prefixes;
- any future-derived confidence signal.

The runtime guard requires the exact approved context type. Evaluation-only contexts that carry
future information are represented separately and must fail with a machine-readable
`forbidden_future_information_access` violation.

## Consequences

### Easier now

- deterministic causal-safety tests;
- auditable policy inputs;
- negative controls that demonstrate why apparent utility is insufficient;
- later schedulers that cannot accidentally accept retrospective context shapes.

### Cost accepted

- the initial scheduler API is intentionally narrow;
- later experiment features must be introduced through explicit contract changes;
- oracle and retrospective evaluations remain test-only and cannot be reused as runtime inputs.

## Non-claims

Passing this boundary does not itself prove lossless decoding or production correctness. It proves
only that the SpecSafe runtime policy contract does not expose named future or observed fields at
its scheduling boundary.
