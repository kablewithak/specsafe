# V5 Kaggle Candidate Calibrator Independent Holdout Precollection

## Purpose

This document freezes the label-free independent holdout precollection boundary for the retained combined Kaggle candidate calibrator.

PR #123 established the promotion governance decision. This slice prepares the next evidence acquisition step without promoting the calibrator, changing thresholds, tuning a scheduler, or building public Hugging Face proof.

## Current repository evidence

```text
current_branch=main
working_tree=clean
latest_user_reported_commit=44663c8 Merge pull request #123 from kablewithak/docs/calibrator-promotion-holdout-governance
```

## Boundary

```text
boundary=v5_candidate_calibrator_independent_holdout_precollection
data_role=independent_holdout_precollection
evidence_class=kaggle_environment_candidate_holdout_planning
calibrator_promotion_status=not_authorized_pending_independent_holdout_replay
threshold_promotion_status=not_authorized
scheduler_promotion_status=not_authorized
hugging_face_final_release_status=blocked_until_holdout_decision
```

## Files introduced

```text
data/kaggle_holdout/v5_candidate_calibrator_holdout_prompt_corpus.jsonl
data/kaggle_holdout/v5_candidate_calibrator_holdout_precollection_manifest.json
notebooks/kaggle/v5_candidate_calibrator_holdout_collection_readme.md
docs/experiments/v5-kaggle-calibrator-independent-holdout-precollection.md
```

## Prompt corpus summary

```text
corpus_id=v5-qwen-candidate-calibrator-independent-holdout-prompts-v1
prompt_record_count=48
structured_text=16
code=16
open_ended_chat=16
prompt_corpus_sha256=8ca11c0717c45552211cf7b85994caf59a0f5f101735064d28b9fbd98043c56f
manifest_sha256=431bd2fdfb9007bbbf4b91f0e109cb9871b12fa292cc3720b3ecd1465c304af2
```

## Allowed use

- Upload the label-free prompt corpus into a private governed Kaggle holdout collection workflow.
- Collect independent holdout traces using the same governed model/tokenizer boundary as the retained combined calibrator pipeline.
- Retain, analyze, and replay holdout evidence.
- Apply the retained candidate calibrator to the holdout without refit.
- Decide whether the candidate calibrator can be promoted, must remain diagnostic-only, or needs more holdout evidence.

## Forbidden use

- Do not refit the candidate calibrator using holdout prompts, holdout labels, or holdout replay results.
- Do not tune thresholds from holdout results.
- Do not tune scheduler policy from holdout results.
- Do not merge holdout traces into the fit pool before the promotion decision.
- Do not use this as production speed, latency, throughput, cost, or serving evidence.
- Do not build final Hugging Face proof packaging as if promotion has already passed.

## Leakage controls

The prompt corpus is label-free. It contains no observed acceptance outcomes, no calibrated outputs, no threshold decisions, and no scheduler decisions.

Before collection, verify that the selected prompts are not duplicates of fit-pool prompts and are not near-duplicates intentionally derived from known fit-pool prompt text. If duplicate checking requires repository artifacts not present in this slice, run it in the follow-up collection-readiness slice.

## Acceptance gate for this slice

This slice is complete when:

```text
- the prompt corpus is committed;
- the precollection manifest is committed;
- JSON and JSONL parsing checks pass;
- marker checks confirm holdout-only, no-refit, no-threshold-tuning, and no-scheduler-tuning boundaries;
- main is clean after merge.
```

## Next safe action after merge

Prepare the private Kaggle holdout upload/run bundle and duplicate-check gate, then collect the holdout archive.

Do not run calibrator replay or promotion logic until the holdout archive is retained and analyzed.
