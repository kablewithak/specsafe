# V5 Kaggle Candidate Calibrator Holdout Upload/Run Bundle

## Purpose

This slice adds the governed upload/run preparation boundary for the independent holdout
prompt corpus introduced after the calibrator-promotion governance ADR.

It does not collect holdout outcomes, replay the calibrator, tune thresholds, promote the
calibrator, or prepare final public Hugging Face proof packaging.

## Current repository evidence

```text
current_branch=main
working_tree=clean
latest_user_reported_commit=ff5e201 Merge pull request #124 from kablewithak/feat/independent-holdout-precollection
```

## Boundary

```text
boundary=v5_candidate_calibrator_independent_holdout_upload_run_bundle
data_role=independent_holdout_upload_preparation
evidence_class=kaggle_environment_candidate_holdout_planning
calibrator_promotion_status=not_authorized_pending_independent_holdout_replay
threshold_promotion_status=not_authorized
scheduler_promotion_status=not_authorized
hugging_face_final_release_status=blocked_until_holdout_decision
```

## Files introduced

```text
scripts/prepare_kaggle_holdout_upload_bundle.py
tests/test_prepare_kaggle_holdout_upload_bundle.py
notebooks/kaggle/v5_candidate_calibrator_holdout_upload_run_readme.md
docs/experiments/v5-kaggle-calibrator-holdout-upload-run-bundle.md
```

## What the script does

`prepare_kaggle_holdout_upload_bundle.py` validates the frozen holdout prompt corpus and
precollection manifest, then writes a private Kaggle upload ZIP.

The script checks:

- prompt JSONL parses successfully;
- prompt records are strict and label-free;
- manifest prompt count matches the corpus;
- manifest prompt-corpus hash matches the file on disk;
- corpus ID matches between manifest and prompt records;
- duplicate case IDs are rejected;
- exact normalized duplicate prompt text is rejected inside the holdout corpus;
- optional exact normalized duplicate checks can be run against forbidden/reference
  JSONL prompt corpora.

## What the script deliberately does not do

- It does not run Kaggle.
- It does not collect traces.
- It does not inspect holdout labels or outcomes.
- It does not replay the candidate calibrator.
- It does not refit the candidate calibrator.
- It does not tune thresholds.
- It does not tune scheduler policy.
- It does not produce public release artifacts.

## Recommended local dry run

Use a temporary output directory so generated upload artifacts do not dirty the repository:

```powershell
$output = Join-Path $env:TEMP "specsafe_candidate_calibrator_holdout_upload_bundle"
Remove-Item $output -Recurse -Force -ErrorAction SilentlyContinue
python .\scripts\prepare_kaggle_holdout_upload_bundle.py --output-dir $output
Get-ChildItem $output
```

## Optional forbidden-corpus duplicate check

If a prior fit-pool prompt corpus exists as JSONL with `prompt_text` fields, pass it as a
forbidden reference:

```powershell
python .\scripts\prepare_kaggle_holdout_upload_bundle.py `
  --output-dir $output `
  --forbidden-corpus .\path	oit_pool_prompt_corpus.jsonl
```

This check is exact after whitespace collapse and case folding. It is not a semantic
near-duplicate detector and must not be described as proving prompt-family independence.

## Acceptance gate for this slice

```text
- upload bundle script committed;
- script tests committed;
- script dry-run produces a Kaggle upload ZIP in a temporary output directory;
- targeted pytest passes;
- Ruff lint and format gates pass;
- candidate calibrator remains not authorized for promotion.
```

## Claims permitted after merge

```text
SpecSafe has a governed local script for preparing a private Kaggle holdout upload bundle
from the frozen independent holdout prompt corpus.
```

## Claims forbidden after merge

```text
- independent holdout performance;
- calibrator promotion;
- threshold promotion;
- scheduler promotion;
- adaptive-policy utility improvement;
- Hugging Face final public proof release;
- production speed, latency, throughput, cost, or serving readiness.
```

## Next safe action

After this PR merges, run the script locally to create the private Kaggle upload ZIP,
then use the notebook-facing runbook to perform governed private Kaggle holdout trace
collection. The next repository slice after collection should retain the holdout archive,
not replay or promote from unretained outputs.
