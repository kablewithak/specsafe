# SpecSafe V5 Qwen Trace Collection V2 Readiness

This directory contains the readiness boundary for the second governed Kaggle
trace collection.

The readiness bundle is generated from:

```text
evidence/kaggle-trace-collection/v5-qwen-governed-trace-collection-v2/pre-collection/pre_collection_manifest.json
```

It writes:

```text
evidence/kaggle-trace-collection/v5-qwen-governed-trace-collection-v2/readiness/collection_readiness_bundle.json
```

## Boundary

This slice prepares the notebook/run contract only. It does not run model inference, does not collect a second archive, does not fit a Kaggle-derived calibrator, does not promote thresholds, and does not support a production speedup or production-serving claim.

## Required controls for the later Kaggle run

- Use the retained pre-collection manifest without editing prompt splits.
- Record exact model and tokenizer revisions.
- Record Kaggle GPU and package versions.
- Export runtime records separately from expected outcomes.
- Retain only sanitized archive artifacts and manifests.
- Do not print or commit tokens, secrets, credentials, or raw private payloads.

## Local readiness command

```powershell
python .\scripts\prepare_kaggle_trace_collection_readiness_bundle.py
python -m pytest .\tests\test_kaggle_trace_collection_readiness_bundle.py
```

## Next safe action

After this slice is merged, the next safe action is the actual second Kaggle
collection run using the readiness bundle. The run must produce a retained
archive before any local analysis, replay, or calibration diagnostic work.
