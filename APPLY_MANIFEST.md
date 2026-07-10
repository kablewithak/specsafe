# Apply Manifest — V5 Candidate Calibrator Independent Holdout Precollection

## Files

```text
data/kaggle_holdout/v5_candidate_calibrator_holdout_prompt_corpus.jsonl
data/kaggle_holdout/v5_candidate_calibrator_holdout_precollection_manifest.json
notebooks/kaggle/v5_candidate_calibrator_holdout_collection_readme.md
docs/experiments/v5-kaggle-calibrator-independent-holdout-precollection.md
```

## Hashes

```text
prompt_corpus_sha256=8ca11c0717c45552211cf7b85994caf59a0f5f101735064d28b9fbd98043c56f
precollection_manifest_sha256=431bd2fdfb9007bbbf4b91f0e109cb9871b12fa292cc3720b3ecd1465c304af2
```

## Validation

```powershell
python -m json.tool .\data\kaggle_holdout\v5_candidate_calibrator_holdout_precollection_manifest.json | Out-Null
Get-Content .\data\kaggle_holdout\v5_candidate_calibrator_holdout_prompt_corpus.jsonl | ForEach-Object { $_ | ConvertFrom-Json | Out-Null }
git diff --check
```
