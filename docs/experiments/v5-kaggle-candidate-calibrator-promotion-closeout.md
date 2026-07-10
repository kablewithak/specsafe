# V5 Kaggle Candidate-Calibrator Promotion Closeout

## Decision

```text
decision_outcome=KEEP_DIAGNOSTIC_ONLY
promotion_attempt_status=closed_not_promoted
candidate_disposition=retained_diagnostic_negative_evidence
calibrator_promotion_status=not_authorized_closed_ranking_safety_regression
```

## Evidence Reviewed

```text
source_replay_report=v5-qwen-candidate-calibrator-independent-holdout-replay-v1
source_replay_run=v5-qwen-candidate-calibrator-independent-holdout-replay-run-001
candidate_calibrator=v5-qwen-combined-fixed-bin-isotonic-calibrator-v1
holdout_archive=v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4
holdout_records=192
holdout_positives=136
holdout_negatives=56
```

## Result

```text
brier_improvement=0.03811936896716564
fixed_bin_ece_improvement=0.10713044469407718
auroc_delta=-0.024356617647058765
maximum_allowed_auroc_degradation=0.001
failure_label=ranking_safety_regression
```

The candidate improved aggregate Brier score and fixed-bin ECE but exceeded the declared ranking-safety degradation budget.

The replay recommendation is adopted without modification.

## Operational Boundary

```text
automated_scheduling_confidence_status=unfit_use_conservative_fallback
threshold_promotion_status=not_authorized
scheduler_promotion_status=not_authorized
public_release_status=bounded_negative_evidence_only
production_claim_status=not_authorized
```

The current holdout is consumed promotion evidence. It cannot be used for refitting, threshold tuning, scheduler tuning, or future fit-pool augmentation.

## Why This Matters

The closeout demonstrates a production-shaped reliability behavior: a candidate can improve attractive aggregate metrics and still be rejected because a separate safety property regressed.

The commercial proof is not that the calibrator succeeded. The proof is that the evaluation harness prevented an unsafe promotion that a simpler dashboard could have approved.

## Next Authorized Work

```text
- package the negative result with explicit non-promotion labels
- or open a fresh calibrator-redesign protocol with fresh fit and holdout evidence
```

The current candidate remains useful as a regression fixture and public negative-evidence example only.
