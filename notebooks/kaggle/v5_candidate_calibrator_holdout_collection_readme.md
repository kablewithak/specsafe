# V5 Candidate Calibrator Holdout Collection README

## Role

This notebook-facing README describes how the independent holdout prompt corpus should be used in the private Kaggle collection step.

This is not a public demo, not a production benchmark, and not a Hugging Face release artifact.

## Inputs

```text
data/kaggle_holdout/v5_candidate_calibrator_holdout_prompt_corpus.jsonl
data/kaggle_holdout/v5_candidate_calibrator_holdout_precollection_manifest.json
```

## Collection requirements

- Reuse the same governed Qwen model-pair and tokenizer boundary from the latest retained Kaggle collection manifest.
- Record exact model IDs, model revisions, tokenizer ID, tokenizer revision, package versions, hardware environment, seed, and notebook revision.
- Export traces using the governed Kaggle trace schema already used by the combined calibrator pipeline.
- Keep the runtime policy context narrower than the full trace schema.
- Use labels only after trace decisions are recorded and only for holdout scoring/replay.
- Do not refit the candidate calibrator.
- Do not tune thresholds.
- Do not tune scheduler policy.
- Do not print secrets.
- Do not publish raw notebook working directories.

## Expected follow-up artifacts

The collection step should eventually produce a retained archive and analysis/replay artifacts equivalent in discipline to earlier Kaggle collection slices.

Required future outputs:

```text
retained_holdout_archive
holdout_archive_manifest
holdout_analysis_report
candidate_calibrator_holdout_replay_report
promotion_decision_report
```

## Decision outputs

Exactly one of these decisions should be made after retained holdout replay:

```text
PROMOTE_CANDIDATE_CALIBRATOR
KEEP_CANDIDATE_CALIBRATOR_DIAGNOSTIC_ONLY
REQUIRE_ADDITIONAL_HOLDOUT_EVIDENCE
```

Any promotion decision must state calibration metrics, negative count, sample count, data role, replay command, artifact hashes, and non-claims.
