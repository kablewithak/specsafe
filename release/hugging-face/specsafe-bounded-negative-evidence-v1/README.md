---
license: cc-by-4.0
pretty_name: SpecSafe Bounded Negative-Evidence Release v1
tags:
  - ai-reliability
  - calibration
  - evaluation
  - negative-results
  - governance
---

# SpecSafe Bounded Negative-Evidence Release

## Validity marker

```text
CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY
```

## Release status

```text
release_id=specsafe-bounded-negative-evidence-v1
release_type=bounded_negative_evidence
publication_status=local_pack_only
candidate_not_promoted=true
threshold_promotion_authorized=false
scheduler_promotion_authorized=false
production_claim_authorized=false
```

This local pack presents a governed negative result. It does not present the retained candidate as a successful calibrator or as trusted input for automated scheduling.

## What was evaluated

- Candidate artifact: `v5-qwen-combined-fixed-bin-isotonic-calibrator-v1`.
- Independent holdout records: `192`.
- Positive outcomes: `136`.
- Negative outcomes: `56`.
- Replay mode: frozen candidate applied without refit.

## Aggregate holdout metrics

| Metric | Raw | Calibrated | Movement |
|---|---:|---:|---:|
| Brier score | 0.187478052189 | 0.149358683222 | 0.0381193689672 |
| Fixed-bin ECE | 0.206981080138 | 0.0998506354439 | 0.107130444694 |
| AUROC | 0.881827731092 | 0.857471113445 | -0.0243566176471 |

Brier score and fixed-bin ECE improved. AUROC decreased by more than the declared ranking-safety tolerance, so the higher-priority gate blocked promotion.

## Decision

```text
decision_outcome=KEEP_DIAGNOSTIC_ONLY
promotion_attempt_status=closed_not_promoted
candidate_disposition=retained_diagnostic_negative_evidence
failure_label=ranking_safety_regression
conservative_fallback_required=true
```

## Supported claims

- The candidate completed independent holdout replay without refit.
- The candidate improved aggregate Brier score and fixed-bin ECE on holdout.
- The candidate regressed ranking safety beyond the declared tolerance.
- The promotion attempt is closed and the candidate is not promoted.
- The retained result is diagnostic negative evidence.

## Forbidden claims

- The current candidate calibrator is promoted.
- The current calibrated probabilities are fit for automated scheduling.
- Any threshold or scheduler is promoted from the current holdout.
- Adaptive-policy utility improvement is proven.
- Public artifacts demonstrate positive promotion proof.
- Production speed, latency, throughput, cost, or serving readiness is proven.

## Data and privacy

This pack contains aggregate metrics and governed decision metadata only. It contains no raw prompts, private or customer records, secrets, raw model outputs, environment dumps, user-input collection, or live inference.

## Reproduction

From the SpecSafe repository root:

```powershell
python .\scripts\build_bounded_negative_evidence_release.py --check
```

The command verifies source hashes, strict source schemas, cross-report identity, canonical release bytes, the manifest, sanitization, and claim boundaries.

## Publication boundary

This directory is a local release candidate only. Public publication requires a separate license, hash, sanitization, dataset-card, visibility, and rollback review.
