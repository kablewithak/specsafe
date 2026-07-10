# Evidence Boundary

## Interpretation

```text
validity_marker=CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY
probability_quality_improved=true
ranking_safety_passed=false
promotion_blocked=true
conservative_fallback_required=true
```

The retained candidate improved aggregate probability-quality metrics but failed the predeclared ranking-safety gate. The correct outcome is rejection for automated probability-driven control, not selective reporting of the favorable metrics.

## Included

- Aggregate holdout counts and probability metrics.
- Candidate, holdout, replay-report, and closeout-decision identities and hashes.
- The retained failure label and non-promotion decision.
- Consumed-holdout rules, supported claims, and forbidden claims.

## Excluded

- Raw prompt or trace content.
- Raw model outputs, notebook outputs, credentials, or environment dumps.
- Private, client, or customer records.
- Threshold selection, scheduler configuration, or live model inference.
- Production speed, latency, throughput, cost, or serving-readiness evidence.

## Holdout consumption

- `do_not_refit_current_candidate_from_holdout`
- `do_not_tune_thresholds_from_holdout`
- `do_not_merge_holdout_into_future_fit_pool`
- `preserve_holdout_as_consumed_promotion_evidence`

The consumed holdout cannot be used to select a replacement method, refit the current candidate, tune thresholds, tune a scheduler, or augment a future fit pool.

## Publication status

```text
publication_status=local_pack_only
license_selection_pending=true
explicit_publication_authorization_required=true
```
