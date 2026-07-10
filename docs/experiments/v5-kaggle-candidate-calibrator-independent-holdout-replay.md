# V5 Candidate Calibrator Independent Holdout Replay

## Result

The retained candidate calibrator was replayed exactly as stored against the retained independent
Kaggle holdout archive. No fit path, bin update, threshold selection, scheduler execution, or
capacity-policy change occurred.

```text
holdout_replay_status=completed_with_ranking_safety_regression
promotion_recommendation=KEEP_DIAGNOSTIC_ONLY
calibrator_promotion_status=not_authorized_ranking_safety_regression
```

## Frozen inputs

```text
candidate_calibrator=v5-qwen-combined-fixed-bin-isotonic-calibrator-v1
candidate_artifact_sha256=e799e4c1e5db8798120b73e0c7e33b86e0f4f220b6360ad010cd0a5feb55ec36
holdout_archive=v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4
holdout_archive_sha256=3ab63ecd516be39ead9901ccc99d1d7a90f09bb2dcde5ca01bd5e258dfa03279
holdout_records=192
holdout_positives=136
holdout_negatives=56
```

The holdout corpus was frozen before collection and is separate from the two archives used to fit
the candidate calibrator.

## Aggregate diagnostics

| Metric | Raw | Candidate calibrated | Delta / interpretation |
|---|---:|---:|---:|
| Brier score | 0.18747805218884495 | 0.1493586832216793 | +0.03811936896716564 improvement |
| Fixed-bin ECE | 0.20698108013796931 | 0.09985063544389214 | +0.10713044469407718 improvement |
| AUROC | 0.881827731092437 | 0.8574711134453782 | -0.024356617647058765 regression |

The candidate improves aggregate probability quality but collapses distinct raw-confidence values
into piecewise-constant calibrated blocks. The resulting ties reduce ranking discrimination beyond
the existing maximum AUROC degradation of `0.001`.

## Gate decision

Passed:

```text
- holdout provenance and independence
- retained file hash checks
- replay-ready archive analysis
- record and negative-count coverage
- frozen candidate artifact integrity
- no-refit boundary
- Brier improvement
- fixed-bin ECE improvement
- threshold-preview support
- bounded claims
```

Failed:

```text
ranking_safety_regression
```

Therefore:

```text
promotion_recommendation=KEEP_DIAGNOSTIC_ONLY
```

The candidate is retained as useful negative evidence. It is not promoted for automated confidence
control.

## Threshold preview boundary

Thresholds `0.50`, `0.60`, `0.70`, `0.80`, `0.90`, and `0.95` are retained only as diagnostic
previews. Their counts must not be used to tune or promote a threshold from this holdout.

## Claims permitted

- The retained candidate calibrator was replayed without refit on independent holdout evidence.
- Aggregate holdout Brier score and fixed-bin ECE improved.
- Holdout ranking safety regressed beyond the declared tolerance.
- The candidate remains diagnostic-only.

## Claims forbidden

- Candidate calibrator promotion.
- Threshold or scheduler promotion.
- Adaptive-policy utility improvement.
- Final Hugging Face proof release authorization.
- Production speed, latency, throughput, cost, or serving-readiness claims.

## Next gate

Create a formal candidate-calibrator promotion closeout decision. The expected direction is to keep
this piecewise-constant candidate as retained negative evidence and decide whether a materially
different rank-preserving calibration route is authorized or the adaptive-calibration path closes.
