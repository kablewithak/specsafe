# Apply Manifest — Candidate-Calibrator Promotion Closeout

## Slice

```text
branch=feat/candidate-calibrator-promotion-closeout
commit=feat: close candidate calibrator promotion
base_main=cd1780f
```

## Files

```text
src/specsafe/candidate_calibrator_closeout/__init__.py
src/specsafe/candidate_calibrator_closeout/models.py
src/specsafe/candidate_calibrator_closeout/decision.py
scripts/close_candidate_calibrator_promotion.py
tests/test_candidate_calibrator_promotion_closeout.py
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/candidate_calibrator_promotion_closeout_decision.json
docs/adr/ADR-0042-close-candidate-calibrator-promotion.md
docs/experiments/v5-kaggle-candidate-calibrator-promotion-closeout.md
APPLY_MANIFEST.md
```

## Boundary

```text
decision_outcome=KEEP_DIAGNOSTIC_ONLY
promotion_attempt_status=closed_not_promoted
candidate_disposition=retained_diagnostic_negative_evidence
automated_scheduling_confidence_status=unfit_use_conservative_fallback
holdout_reuse=blocked
```
