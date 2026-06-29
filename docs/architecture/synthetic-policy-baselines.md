# Synthetic Policy Baselines

## Purpose

This Phase 2 slice defines three explicit policy controls over individual, validated
`CausalSchedulerContext` values. The policies are deterministic and local-only. They
are not a replay evaluator, a calibrated scheduler, a capacity optimiser, or a claim of
utility improvement.

## Valid baseline boundary

The two valid policies share one runtime boundary:

```text
object supplied to policy
  -> require_causal_runtime_context(...)
  -> exact CausalSchedulerContext
  -> typed VerificationDecision with causal_safety_status=pass
```

They cannot accept `SyntheticTraceReplayCase`, expected outcomes, candidate token IDs,
or `RetrospectiveEvaluationContext`. The causal gate rejects non-approved context types
before policy logic executes.

### Fixed-length baseline

`FixedLengthVerificationPolicy` admits a position when:

```text
block_position_index <= maximum_verification_length
```

It intentionally ignores confidence, capacity, outcomes, and workload class. Its role
is to be a blunt, inspectable comparison point.

### Static-threshold baseline

`StaticThresholdVerificationPolicy` admits a position when:

```text
conditional_survival_confidence >= minimum_conditional_survival_confidence
```

It uses the lawful pre-sample confidence present in the exact runtime context. It is
capacity-blind and does not claim confidence calibration. Its threshold is a declared
configuration, not a result of final-evaluation tuning.

## Unsafe retrospective negative control

`UnsafeRetrospectiveLookaheadPolicy` exists only in the test-only control path. It
accepts the exact `RetrospectiveEvaluationContext`, reads `future_acceptance_outcomes`,
and marks every resulting `VerificationDecision` with:

```text
causal_safety_status=fail
```

It demonstrates why apparent policy quality cannot override causal validity. It must not
be wired into a valid policy runner, report headline, promotion gate, or deployment path.

## Evidence and non-claims

This slice proves that the project has deterministic, typed, causally gated blunt
baselines plus an explicitly invalid negative control. It does not prove that any policy
improves utility, reduces verification waste, handles load, uses calibrated confidence,
or behaves safely in production.

A later replay-harness slice must apply policies to the same immutable fixture inputs,
score decisions against post-hoc outcomes, display causal status, and preserve neutral or
losing results.
