# ADR-0039: Govern the Expanded Kaggle Trace Corpus Before Calibration Fitting

## Status

Proposed

## Context

SpecSafe has retained a first governed Kaggle trace archive from real Qwen model execution over a self-authored controlled prompt corpus. The archive has been analyzed, replayed, and calibration-diagnosed.

The diagnostic result is directionally supportive but too small for a retained Kaggle-derived calibrator:

- runtime records: 24
- expected outcome records: 24
- target argmax matches: 15
- target argmax nonmatches: 9
- minimum records required before calibration fitting: 100
- minimum positives required before calibration fitting: 30
- minimum negatives required before calibration fitting: 30

The next safe action is therefore not threshold promotion, calibration fitting, public release, or production-claim expansion. The next safe action is to design a larger, governed, public-safe trace corpus and second collection procedure that can satisfy the calibration-readiness minimums without leaking target-derived outcomes into runtime policy design.

## Decision

SpecSafe will add an explicit planning boundary for the expanded Kaggle trace corpus before any second collection run is treated as calibration-fit eligible.

The expanded corpus design must satisfy these controls before a second governed Kaggle collection is authorized:

1. **Public-safe source boundary**
   - Use only self-authored prompts or explicitly license-compatible public prompts.
   - Do not include private prompts, client data, PII, secrets, private source code, customer artifacts, or sensitive logs.
   - Prefer short prompts with minimized text where raw prompt text is necessary.

2. **Prompt/task-level split discipline**
   - Split at the prompt or task-family level, not at the token or candidate-position level.
   - Related variants must not be spread across calibration and held-out roles merely to inflate sample count.
   - The split role for each planned prompt family must be declared before model outcomes are collected.

3. **Record-count planning**
   - The planned collection must target at least 100 runtime records.
   - The plan must target at least 30 positive and 30 negative target-argmax outcome records.
   - The plan must include contingency capacity for additional prompts if class balance is weaker than expected.

4. **Outcome-separation boundary**
   - Runtime-visible fields remain separate from target-derived outcome labels.
   - Target probabilities, target argmax match labels, and replay outcomes may be used only for post-hoc diagnostics until a later gate explicitly authorizes fitting.
   - No threshold or scheduler promotion is allowed from this planning slice.

5. **Workload coverage**
   - Include structured text, code-like, and open-ended chat task families.
   - Include easy, medium, and hard confidence regimes by design, but do not select or rebalance cases after reviewing target outcomes.

6. **Retention and reproducibility**
   - The second collection must retain a manifest, environment notes, model pair identifiers, tokenizer identifiers, seed/configuration, record counts, artifact hashes, and known limitations.
   - Local deterministic analysis, replay, and calibration diagnostic scripts remain the post-collection gate.

## Consequences

### What this permits

- A larger second Kaggle trace-collection design.
- A prompt/task-family split plan before outcome observation.
- A clear readiness gate for deciding whether a later Kaggle-derived calibration fit is even eligible.

### What this forbids

- Fitting a Kaggle-derived calibrator from the 24-record archive.
- Tuning thresholds on the retained Kaggle archive.
- Promoting a Kaggle threshold policy.
- Publishing a Hugging Face Dataset or Space from this slice.
- Claiming production speedup, production latency, production throughput, production readiness, or natural-workload generalization.

### Residual risk

The second corpus may still fail to produce enough negatives, enough positives, or stable calibration behavior. That is acceptable evidence. The project must retain the result honestly rather than rebalancing after outcomes are known to make the calibration story look stronger.

## Implementation notes

This ADR is a governance and authorization document. It does not change runtime policy code, retained reports, calibration artifacts, thresholds, schedulers, or public release artifacts.

The immediate companion document is:

```text
docs/experiments/v5-kaggle-trace-corpus-expansion-plan.md
```

## Acceptance gate

This ADR is accepted only if the companion plan defines:

- public-safe data/source constraints;
- prompt/task-level split discipline;
- target record count and class-balance minimums;
- workload-family coverage;
- forbidden work;
- second-collection readiness checklist;
- post-collection diagnostic gates;
- claims permitted and forbidden after the planning slice.
