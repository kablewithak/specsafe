# Architecture Map

## Core flow

```text
versioned trace fixture
  -> confidence feature boundary
  -> calibration
  -> causal scheduler context
  -> capacity-aware policy decision
  -> trace replay evaluation
  -> machine-readable result + human-readable report
```

## Planned package boundaries

| Package | Responsibility |
|---|---|
| `contracts` | Pydantic models, enums, error envelopes, trace schema |
| `calibration` | Raw versus calibrated confidence and fitness metrics |
| `scheduling` | Fixed, threshold, causal adaptive, and negative-control policies |
| `capacity_profiles` | Synthetic and Kaggle-measured capacity curves |
| `causal_safety` | Allowed-information boundaries and forbidden-access checks |
| `trace_replay` | Deterministic replay of immutable traces |
| `eval_harness` | Metrics, comparisons, regression gates, and failure taxonomy |
| `reporting` | JSON and Markdown reports for technical and buyer audiences |

## Boundary rule

Model or notebook code may produce trace artifacts. It must not become a hidden dependency of scheduler correctness tests. The core library must be runnable against versioned local fixtures.
