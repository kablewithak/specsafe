# Kaggle Negative-Case Expansion V1 — Authoring Ledger

## Purpose

This corpus is a planned, self-authored negative-case expansion corpus for a third governed Kaggle trace collection.

It exists because the retained v2 calibration diagnostic was directionally supportive but blocked calibration fitting on negative-count grounds:

```text
observed_record_count=120
observed_positive_count=97
observed_negative_count=23
minimum_negative_count_for_calibration_fit=30
calibration_fit_authorized=false
```

## Boundary

This is not model evidence. It is a pre-collection fixture.

Do not use this corpus to fit a Kaggle-derived calibrator, tune thresholds, promote scheduler utility, publish public artifacts, or claim production speedup.

## Authoring controls

- Prompts are self-authored and public-safe.
- No private prompts, client data, secrets, credentials, personal data, or raw sensitive payloads are allowed.
- Prompt-family split discipline is preserved.
- Runtime labels and target outcomes do not exist before model execution.
- Any post-collection calibration decision requires a separate diagnostic gate.

## Planned shape

```text
planned_prompt_count=16
planned_candidate_positions_per_prompt=4
planned_runtime_records=64
minimum_additional_negative_records_needed=7
```

## Workload balance

The corpus intentionally favors higher-entropy cases while retaining workload coverage:

```text
open_ended_chat=6 prompts
code=6 prompts
structured_text=4 prompts
```

## Non-claims

This corpus does not prove calibration fitness, threshold utility, scheduler utility, production speedup, production latency, production throughput, cost savings, public-release readiness, or production readiness.
