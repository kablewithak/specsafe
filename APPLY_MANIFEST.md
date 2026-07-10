# Apply Manifest — Independent Holdout Candidate-Calibrator Replay

## Slice

```text
branch=feat/independent-holdout-candidate-calibrator-replay
commit=feat: replay candidate calibrator on independent holdout
base_main=8b0b81b
```

## Files

```text
src/specsafe/independent_holdout_replay/__init__.py
src/specsafe/independent_holdout_replay/models.py
src/specsafe/independent_holdout_replay/replay.py
scripts/replay_candidate_calibrator_on_independent_holdout.py
tests/test_independent_holdout_candidate_calibrator_replay.py
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/candidate_calibrator_holdout_replay_report.json
docs/experiments/v5-kaggle-candidate-calibrator-independent-holdout-replay.md
APPLY_MANIFEST.md
```

## Boundary

```text
candidate_calibrator_refit=false
threshold_tuning=false
scheduler_execution=false
promotion_recommendation=KEEP_DIAGNOSTIC_ONLY
calibrator_promotion_status=not_authorized_ranking_safety_regression
```
