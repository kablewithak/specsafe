# V5 Kaggle Trace Corpus Expansion Plan

## Purpose

This document defines the next governed SpecSafe step after the first retained Kaggle trace archive and calibration diagnostic gate.

The first archive produced real-model measured behavior in a documented Kaggle environment, but it has only 24 runtime records, 15 positive target-argmax matches, and 9 negative target-argmax nonmatches. That is not enough to fit or retain a Kaggle-derived calibrator.

The purpose of this plan is to design a larger second collection that can be evaluated for calibration-fit readiness without weakening the causal-information boundary, split discipline, or evidence claims.

## Current boundary

Current maturity label:

```text
kaggle_environment_evaluated
```

Current authorized action:

```text
trace-corpus expansion planning and governed second collection design
```

Current blocked actions:

```text
calibration fitting
threshold promotion
scheduler promotion from Kaggle traces
public dataset release
Hugging Face Space release
production speedup or production-readiness claims
```

## Minimum readiness targets

The expanded corpus should target enough records to make a later calibration diagnostic meaningful.

Minimum gate before any future Kaggle-derived calibration fit is considered:

| Requirement | Minimum |
|---|---:|
| Runtime records | 100 |
| Expected outcome records | 100 |
| Positive target-argmax matches | 30 |
| Negative target-argmax nonmatches | 30 |

Planning target:

```text
planned_prompt_families=30
planned_candidate_positions_per_family=4
planned_runtime_records=120
contingency_prompt_families=10
contingency_candidate_positions=40
maximum_planned_records_if_contingency_used=160
```

Rationale:

- 120 planned records gives room above the 100-record floor.
- 40 contingency records protect against unexpectedly weak class balance.
- The 30/30 class-balance target must be checked only after collection; it must not be forced by outcome-aware prompt replacement.

## Prompt-family design

The second corpus should be authored at the prompt-family level.

Each prompt family should declare:

- `prompt_family_id`
- `workload_type`
- `difficulty_intent`
- `expected_confidence_regime`
- `split_role`
- `source_type`
- `privacy_classification`
- `authoring_note`

Recommended workload allocation:

| Workload type | Planned families | Planned records |
|---|---:|---:|
| structured_text | 10 | 40 |
| code_like | 10 | 40 |
| open_ended_chat | 10 | 40 |
| contingency_mixed | 10 | 40 |

Recommended confidence-regime coverage:

| Regime | Purpose |
|---|---|
| high_confidence_easy | Capture likely matches and stable prefixes. |
| medium_confidence_ambiguous | Capture useful ranking separation. |
| low_confidence_hard | Capture likely nonmatches and early failure. |
| mixed_suffix_decay | Capture cases where early positions are easier than later suffixes. |

## Split discipline

Splits are declared before model outcomes are collected.

Allowed split roles:

```text
trace_collection_diagnostic
calibration_candidate
heldout_candidate
adversarial_regression_candidate
```

Rules:

1. Split at prompt-family level, not candidate-position level.
2. Do not place close paraphrases across different future split roles.
3. Do not move prompt families after reviewing target outcomes.
4. Do not tune thresholds, calibration parameters, or prompt selection using held-out candidate outcomes.
5. Do not treat this planning document as evidence that a fit is authorized.

Initial recommended allocation:

| Split role | Prompt families | Planned records | Purpose |
|---|---:|---:|---|
| trace_collection_diagnostic | 6 | 24 | Verify second-run plumbing and corpus behavior. |
| calibration_candidate | 12 | 48 | Candidate pool for possible later fit if readiness passes. |
| heldout_candidate | 8 | 32 | Candidate pool for later evaluation if a fit is separately authorized. |
| adversarial_regression_candidate | 4 | 16 | Preserve hard cases and failure modes. |

The contingency families should remain unassigned until the diagnostic count and class balance are known. If used, the reason must be recorded before any calibration fitting decision.

## Public-safety and privacy controls

The corpus must use only:

- self-authored prompts;
- license-compatible public prompts, if explicitly documented;
- synthetic diagnostic prompts with no private or personal content.

The corpus must not include:

- PII;
- secrets;
- credentials;
- private prompts;
- client data;
- private source code;
- sensitive logs;
- raw customer artifacts;
- `.env` values;
- API keys;
- session tokens.

Publication posture:

```text
not_public_release_ready
```

A later public-release review must decide what prompt text, token IDs, aggregates, manifests, and reports are safe to publish.

## Causal-information boundary

Runtime-visible fields may include only decision-time information.

Allowed runtime-facing fields include:

- trace/request metadata;
- workload type;
- decode round;
- block position index;
- visible prefix token IDs;
- draft probability or raw confidence available before the decision;
- capacity snapshot, if applicable.

Evaluation-only fields include:

- target probability;
- target argmax match label;
- observed target outcome;
- replay mismatch count;
- post-hoc threshold selected/not-selected status;
- calibration diagnostic labels.

Evaluation-only fields must not feed runtime policy decisions, prompt-family selection, or threshold promotion.

## Second collection readiness checklist

Before running or retaining a second collection, confirm:

- [ ] Prompt families are authored and reviewed as public-safe.
- [ ] Prompt-family split roles are declared before outcome observation.
- [ ] The planned corpus targets at least 100 records.
- [ ] The plan includes class-balance readiness targets of at least 30 positives and 30 negatives.
- [ ] The notebook or collection script records model IDs, tokenizer IDs, revisions, seed, decoding configuration, package versions, and Kaggle environment metadata.
- [ ] Runtime records and expected outcome records are separated.
- [ ] No calibration fitting is performed in the collection notebook.
- [ ] No threshold promotion is performed in the collection notebook.
- [ ] Retention manifest and artifact hashes are produced.
- [ ] Local deterministic analysis, replay, and calibration diagnostic are the next gate after retention.

## Post-collection diagnostic gates

After a second archive is collected and retained, run the existing local gates in order:

1. Archive/schema validation.
2. Trace analysis.
3. Diagnostic threshold replay.
4. Calibration-readiness diagnostic.
5. Public-safety review before any publication step.

A future calibration fit may be considered only if the readiness diagnostic confirms:

- record count is sufficient;
- positive count is sufficient;
- negative count is sufficient;
- signal remains directionally useful;
- split discipline is intact;
- no target-derived leakage was introduced.

## Claims ledger

Claims permitted after this planning slice:

- SpecSafe has a governed plan for expanding the Kaggle trace corpus.
- The plan defines public-safety controls, split discipline, readiness targets, and post-collection gates.

Claims explicitly forbidden after this planning slice:

- A Kaggle-derived calibrator has been fit.
- A Kaggle-derived threshold policy has been promoted.
- Adaptive scheduling wins on Kaggle traces.
- The project is production-ready.
- The project shows production speedup, latency reduction, throughput, or cost savings.
- The corpus is ready for public Hugging Face release.

Evidence required before stronger claims:

- A second retained Kaggle trace archive.
- Deterministic local analysis over the retained archive.
- Diagnostic replay over the retained archive.
- Calibration-readiness report proving sample and class-balance thresholds.
- Separate authorization before any calibration fitting or public release.

## Next safe action after this slice

If this planning slice is merged, the next safe action is to author the expanded prompt-family corpus and its pre-collection manifest under the controls in ADR-0039.
