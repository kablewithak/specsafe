# Apply Manifest — Bounded Negative-Evidence Release Pack

## Branch

```text
feat/bounded-negative-evidence-release-pack
```

## Files to add

```text
src/specsafe/bounded_negative_evidence/__init__.py
src/specsafe/bounded_negative_evidence/models.py
src/specsafe/bounded_negative_evidence/builder.py
scripts/build_bounded_negative_evidence_release.py
tests/test_bounded_negative_evidence_release.py
release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/README.md
release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/evidence_boundary.md
release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/release_summary.json
release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/release_manifest.json
docs/experiments/bounded-negative-evidence-release-result.md
APPLY_MANIFEST.md
```

## Source boundary

The builder consumes only these retained committed artifacts:

```text
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/candidate_calibrator_holdout_replay_report.json
evidence/kaggle-trace-collection/v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/candidate_calibrator_promotion_closeout_decision.json
```

Expected source hashes:

```text
candidate_calibrator_holdout_replay_report.json
402df4475b05eead800a5ba7f6b4ae96587fd5bfbe83f20966ac180888e1467f

candidate_calibrator_promotion_closeout_decision.json
e91047e78f8992e252d3f313943ff8e86aafd2c1c77b3683058d2406a29266bc
```

## Retained release status

```text
release_id=specsafe-bounded-negative-evidence-v1
validity_marker=CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY
publication_status=local_pack_only
candidate_not_promoted=true
threshold_promotion_authorized=false
scheduler_promotion_authorized=false
production_claim_authorized=false
```

## Local pre-delivery validation

```text
8 focused tests passed in an isolated repository replica
Ruff lint passed with Ruff 0.15.20
Ruff format check passed with Ruff 0.15.20
canonical release-pack check passed
```

The authoritative full-suite result is the user's local repository validation after applying this
slice.
