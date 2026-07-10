# ADR-0049: Freeze the Hugging Face Space Evidence Index

## Status

Accepted.

## Context

The public Dataset is verified and its publication receipt is retained at merge commit `ec70bba`.
The next product layer is a visually polished Hugging Face Space, but the UI must not independently
reinterpret large research artifacts or drift from the governed result.

## Decision

Create one deterministic, read-only evidence index for:

```text
space_repository_name=specsafe-reliability-lab
space_title=SpecSafe — When Should AI Spend More Compute?
short_description=AI reliability case study on adaptive verification.
```

The index is derived from three exact SHA-256-bound sources:

```text
controlled synthetic comparison=e82e21853526e687b068cd8a0b3abb4bb390da755be977bf5f3045148a7d17f4
bounded negative-evidence summary=264886c6bb6d2490bb95b43a29506b04437972e5a42c6688db7dc7d124f8df90
Dataset publication receipt=a63cd76cefa376fc4baa108f4d0fa06b66ed2c4561cea29f3ac2280837e525b7
```

## Comparison semantics

Case identity remains exact for case ID, split, and capacity profile. Retained utility values use
zero relative tolerance and an absolute tolerance of `1e-12` so harmless JSON floating-point
serialization noise does not masquerade as evidence drift. Any material utility change still fails
closed.

## Evidence boundary

The index retains:

- six valid causal policy comparisons;
- six excluded retrospective unsafe controls;
- adaptive wins, neutral cases, and one loss;
- the exact six case-level utility results;
- the independent holdout calibration metrics;
- the ranking-safety failure and non-promotion decision;
- the verified public Dataset identity and revision;
- concise supported claims and non-claims.

The index permits no live inference, user input, threshold tuning, evidence mutation, or optimizer.

## Presentation consequence

The Space UI will consume this small frozen JSON contract rather than reading raw repository evidence
at runtime. That keeps presentation code simple, testable, reviewable, and disconnected from secrets
or customer data.

## Next step

Build the visually polished, responsive React and shadcn/ui Space shell against the frozen evidence
index. The next slice may implement the interface locally but will not publish the Space.
