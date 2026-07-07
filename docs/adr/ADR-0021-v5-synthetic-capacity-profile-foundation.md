# ADR-0021: Establish a Versioned Synthetic Capacity-Profile Foundation

- **Status:** Accepted
- **Date:** 2026-07-07
- **Scope:** V5 causal-policy foundation
- **Decision owner:** SpecSafe project

## Context

The V5 held-out calibration assessment passed the calibration eligibility gate. That result authorises controlled causal-policy foundation work, but it does not demonstrate policy utility, serving throughput, latency reduction, cost reduction, or production readiness.

The repository already has a lawful runtime `CapacitySnapshot` inside the exact `CausalSchedulerContext` contract. It records the decision-time profile ID, source, active request count, and verification-batch token count. However, no versioned capacity-profile artifact exists yet. Without one, a later policy could hide capacity assumptions inside scheduler code, and replay comparisons could not prove that policies faced identical declared capacity conditions.

## Decision

Create an isolated `specsafe.capacity_profiles` package and a governed V1 fixture set.

The fixture set contains exactly five synthetic profile kinds:

- `light_load`
- `moderate_load`
- `saturated_load`
- `jagged_capacity`
- `flat_capacity_control`

Each profile is immutable, schema-strict, versioned, hash-addressed through a manifest, and explicit about its synthetic provenance and normalized units. A profile deterministically evaluates a lawful `CapacitySnapshot` using:

```text
request_token_load = active_request_count × verification_batch_tokens
```

The profile returns only normalized capacity and marginal verification-cost proxies. These outputs are controlled replay assumptions, not measured hardware behavior.

The package does not introduce scheduler logic, utility scoring, baseline comparison, policy tuning, calibration refitting, or final-evidence changes.

## Consequences

### Positive

- A future load-aware policy can consume declared capacity semantics instead of private heuristics.
- Later replay comparisons can record a stable profile ID, profile version, and configuration hash.
- Flat and jagged controls make it possible to test whether a future policy depends on hidden monotonic assumptions.
- Malformed profiles, hash mismatches, source mismatches, and unknown profile IDs fail explicitly.

### Negative

- The profile curves are synthetic and have no production throughput meaning.
- A later scheduler must still prove causal validity, calibration fitness, and policy utility against valid baselines.
- Capacity profiles alone do not authorise a policy claim.

## Guardrails

- The existing V5 calibration and final-evaluation evidence artifacts remain unchanged.
- A profile must never use final labels, outcomes, or retrospective replay results.
- `KAGGLE_MEASURED` capacity profiles remain out of scope for this slice.
- The unsafe retrospective control remains separate from valid policy paths.
- Any future policy comparison must use identical immutable traces, identical declared profile fixtures, and a shared scorer.

## Acceptance evidence

This ADR is satisfied when:

- strict contracts and fixture manifests load all five named profiles;
- profile lookup is deterministic from a lawful `CapacitySnapshot`;
- flat and jagged behavior is explicitly tested;
- malformed, altered, mismatched, and unknown profile inputs fail with typed codes;
- no V5 frozen evidence hash changes;
- no scheduler, utility, throughput, latency, cost, or production claim is introduced.
