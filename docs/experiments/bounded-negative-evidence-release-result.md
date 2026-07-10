# SpecSafe Bounded Negative-Evidence Release Result

## Result

The deterministic local release pack is retained at:

```text
release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/
```

Its validity marker is:

```text
CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY
```

## Retained decision

```text
probability_quality_improved=true
ranking_safety_passed=false
promotion_blocked=true
conservative_fallback_required=true
decision_outcome=KEEP_DIAGNOSTIC_ONLY
promotion_attempt_status=closed_not_promoted
publication_status=local_pack_only
```

## Aggregate holdout result

```text
holdout_record_count=192
holdout_positive_count=136
holdout_negative_count=56

raw_brier_score=0.18747805218884495
calibrated_brier_score=0.1493586832216793
brier_improvement=0.03811936896716564

raw_fixed_bin_ece=0.20698108013796931
calibrated_fixed_bin_ece=0.09985063544389214
fixed_bin_ece_improvement=0.10713044469407718

raw_auroc=0.881827731092437
calibrated_auroc=0.8574711134453782
auroc_delta=-0.024356617647058765
maximum_allowed_auroc_degradation=0.001
```

The favorable Brier and fixed-bin ECE movement did not override the failed ranking-safety gate.

## Release contents

```text
README.md
evidence_boundary.md
release_summary.json
release_manifest.json
```

The pack contains aggregate metrics and governed decision metadata only. It does not contain raw
prompt or trace content, model payloads, credentials, private data, threshold selection, scheduler
configuration, live inference, or production claims.

## Reproduction

```powershell
python .\scripts\build_bounded_negative_evidence_release.py --check
```

The check validates source hashes, strict source schemas, candidate and holdout identity alignment,
canonical release bytes, file hashes, sanitization, and non-promotion claims.

## Publication boundary

This slice builds and retains a local release candidate. It does not publish to Hugging Face and does
not select a license.

The next gate is a publication-readiness review covering the exact pack hashes, sanitization,
dataset-card wording, license selection, repository visibility, rollback procedure, and explicit
publication authorization.
