# ADR-0001: Establish SpecSafe as a Policy-Evaluation Lab, Not a Serving Engine

- **Status:** Accepted
- **Date:** 2026-06-28

## Context

Speculative decoding research demonstrates that blindly verifying long candidate blocks can waste expensive target-model capacity. It also demonstrates that a scheduler may be invalid when it uses future token-dependent information to decide whether to admit an earlier token for verification.

A faithful end-to-end reproduction of production systems such as DSpark would require trained draft architectures, exact rejection sampling, serving-engine integration, hardware-specific profiling, and live workload conditions. That scope is inappropriate for this project's 50–70 hour budget and would make claims difficult to support.

## Decision

SpecSafe will be built as a deterministic, typed, and reproducible policy-evaluation lab.

The project will:

- replay versioned synthetic and optional small-model trace fixtures;
- compare fixed, static-threshold, causal adaptive, and intentionally unsafe retrospective policies;
- calibrate confidence before allowing it to drive automated scheduling;
- model capacity through explicitly labelled synthetic and Kaggle-measured profiles;
- reject policy results that violate causal non-anticipation requirements;
- publish only sanitized data and trace metadata.

## Consequences

### Easier now

- deterministic tests;
- causal negative controls;
- clean before/after policy evaluation;
- reproducible reports;
- honest public proof.

### Explicitly deferred

- custom GPU kernels;
- production batching and queue integration;
- live-traffic goodput claims;
- a trained DSpark-like drafter;
- deployment as an inference server.

## Non-claims

SpecSafe will not claim to reproduce DSpark, provide production serving throughput, or preserve a target distribution outside the exact experimental conditions where that property is explicitly implemented and tested.
