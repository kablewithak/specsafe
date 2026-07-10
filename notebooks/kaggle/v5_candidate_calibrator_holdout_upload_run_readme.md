# V5 Candidate Calibrator Holdout Upload/Run README

## Role

This README is the private Kaggle collection runbook for the independent holdout upload
bundle.

It is not a public demo, not a production benchmark, and not a Hugging Face release
artifact.

## Local preparation

Create the upload ZIP from the repository-local frozen holdout corpus and manifest:

```powershell
$output = Join-Path $env:TEMP "specsafe_candidate_calibrator_holdout_upload_bundle"
Remove-Item $output -Recurse -Force -ErrorAction SilentlyContinue
python .\scripts\prepare_kaggle_holdout_upload_bundle.py --output-dir $output
Get-ChildItem $output
```

Upload this generated ZIP to the private governed Kaggle notebook:

```text
v5_candidate_calibrator_holdout_kaggle_upload_bundle.zip
```

## Required Kaggle run constraints

- Reuse the same governed Qwen model-pair and tokenizer boundary from the retained
  combined calibrator pipeline.
- Pin and record exact model IDs, model revisions, tokenizer ID, tokenizer revision,
  package versions, hardware environment, seed, and notebook revision.
- Export traces using the governed Kaggle trace schema already used by the combined
  calibrator pipeline.
- Keep runtime policy context narrower than the full trace schema.
- Use labels only after trace decisions are recorded and only for holdout scoring/replay.
- Do not refit the candidate calibrator.
- Do not tune thresholds.
- Do not tune scheduler policy.
- Do not print secrets.
- Do not publish raw notebook working directories.

## Required Kaggle output shape

The private Kaggle run should produce an archive that can later be retained in the
repository through a governed retention slice.

Expected future archive contents:

```text
holdout_runtime_traces.jsonl
holdout_expected_outcomes.jsonl
holdout_collection_manifest.json
holdout_environment_report.json
holdout_archive_checksums.json
```

The exact names may follow the existing repository convention from retained Kaggle
archives, but the retained archive must preserve the same evidence types.

## Stop conditions

Stop and do not promote if any of these occur:

```text
model_pair_tokenizer_mismatch
holdout_manifest_mismatch
holdout_prompt_duplicate_or_related_to_fit_pool
calibrator_refit_detected
threshold_tuning_detected
insufficient_holdout_negative_count
unsupported_promotion_claim
```

## Later decision outputs

Exactly one later promotion decision is allowed after retained independent holdout replay:

```text
PROMOTE_CANDIDATE_CALIBRATOR
KEEP_CANDIDATE_CALIBRATOR_DIAGNOSTIC_ONLY
REQUIRE_ADDITIONAL_HOLDOUT_EVIDENCE
```

A promotion decision must state calibration metrics, negative count, sample count, data
role, replay command, artifact hashes, and non-claims.
