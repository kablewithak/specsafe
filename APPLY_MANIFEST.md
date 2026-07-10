# Apply Manifest — V5 Candidate Calibrator Holdout Upload/Run Bundle

## Files

```text
scripts/prepare_kaggle_holdout_upload_bundle.py
tests/test_prepare_kaggle_holdout_upload_bundle.py
docs/experiments/v5-kaggle-calibrator-holdout-upload-run-bundle.md
notebooks/kaggle/v5_candidate_calibrator_holdout_upload_run_readme.md
```

## Validation

```powershell
$output = Join-Path $env:TEMP "specsafe_candidate_calibrator_holdout_upload_bundle"
Remove-Item $output -Recurse -Force -ErrorAction SilentlyContinue
python .\scripts\prepare_kaggle_holdout_upload_bundle.py --output-dir $output
python -m pytest .	ests	est_prepare_kaggle_holdout_upload_bundle.py
python -m ruff check .
python -m ruff format --check .\scripts\prepare_kaggle_holdout_upload_bundle.py .	ests	est_prepare_kaggle_holdout_upload_bundle.py
git diff --check
```

## Boundary

This slice prepares a private Kaggle upload bundle. It does not collect holdout traces,
replay the candidate calibrator, promote the calibrator, tune thresholds, tune scheduler
policy, or authorize public Hugging Face final proof packaging.
