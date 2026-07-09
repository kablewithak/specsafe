# V5 Kaggle Negative-Case Expansion — Private Upload/Run Bundle

## Purpose

This slice adds the local tooling and notebook-side README for preparing a private Kaggle input dataset for `v5-qwen-negative-case-expansion-v1 / attempt-001-t4`.

The goal is to collect additional nonmatch/negative observations because the v2 calibration diagnostic remained blocked:

- observed records: `120`
- observed positives: `97`
- observed negatives: `23`
- minimum negatives required for calibration fit: `30`
- calibration fit authorized: `false`

## What this slice authorizes

This slice authorizes only preparation of a private Kaggle input ZIP from already retained repo files.

It does not authorize Kaggle inference by itself. The run still has to be executed manually in a private Kaggle notebook after this PR is merged and the upload ZIP is generated from clean `main`.

## Generated local artifacts

Running the script creates:

- `evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/kaggle-input/specsafe_v5_qwen_negative_case_expansion_v1_private_input.zip`
- `evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/kaggle-input/kaggle_input_bundle_manifest.json`

The ZIP uses POSIX paths only. This avoids the previous Kaggle dataset upload failure caused by Windows backslash paths inside the archive.

## Included files

The private input ZIP includes:

- `RUN_SOURCE_COMMIT.txt`
- `UPLOAD_BUNDLE_INPUT_MANIFEST.json`
- `data/fixtures/kaggle_negative_case_expansion_v1/prompt_corpus.json`
- `data/fixtures/kaggle_negative_case_expansion_v1/manifest.json`
- `data/fixtures/kaggle_negative_case_expansion_v1/authoring_ledger.md`
- `evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/pre-collection/pre_collection_manifest.json`
- `evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/readiness/collection_readiness_bundle.json`
- `docs/experiments/v5-kaggle-negative-case-expansion-precollection.md`
- `notebooks/kaggle/specsafe_v5_qwen_negative_case_expansion_v1_README.md`

## Evidence boundary

This is upload-bundle preparation only.

It does not:

- run Kaggle model inference
- collect a third archive
- fit a Kaggle-derived calibrator
- tune or promote thresholds
- promote scheduler utility
- publish public artifacts
- claim production speedup, latency, throughput, cost savings, or production readiness

## Next safe gate

After this PR is merged, generate the private input ZIP from clean `main`, upload it as a private Kaggle dataset, and run the governed negative-case collection notebook.
