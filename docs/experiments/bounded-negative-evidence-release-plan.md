# SpecSafe Bounded Negative-Evidence Release Plan

## Objective

Create a deterministic, sanitized local release pack that communicates why the retained
Kaggle-derived candidate calibrator was rejected after independent holdout replay.

The pack is a proof of the reliability harness, not a positive calibrator-promotion artifact.

## Release identity

```text
release_id=specsafe-bounded-negative-evidence-v1
release_type=bounded_negative_evidence
validity_marker=CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY
candidate_disposition=retained_diagnostic_negative_evidence
publication_status=local_pack_only
```

## Frozen source artifacts

The builder will consume only committed, hash-verified source artifacts:

```text
evidence/kaggle-trace-collection/
  v5-qwen-candidate-calibrator-independent-holdout-v1/
  attempt-001-t4/
  candidate_calibrator_holdout_replay_report.json

evidence/kaggle-trace-collection/
  v5-qwen-candidate-calibrator-independent-holdout-v1/
  attempt-001-t4/
  candidate_calibrator_promotion_closeout_decision.json
```

The builder may read candidate identity and source hashes from those governed reports. It must not
read raw prompts, rerun model inference, refit calibration, or inspect records to select a new
threshold.

## Proposed local output

```text
release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1/
  README.md
  evidence_boundary.md
  release_summary.json
  release_manifest.json
```

No raw archive, JSONL trace file, raw prompt corpus, notebook output, or model payload is copied into
the release directory.

## Release summary fields

The machine-readable summary must retain:

- schema version;
- release ID and type;
- validity marker;
- source commit;
- source report paths and SHA-256 hashes;
- candidate artifact ID and hash;
- holdout archive ID and hash;
- holdout record, positive, and negative counts;
- raw and calibrated Brier score;
- Brier improvement;
- raw and calibrated fixed-bin ECE;
- fixed-bin ECE improvement;
- raw and calibrated AUROC;
- AUROC delta and maximum permitted degradation;
- failure labels;
- promotion decision and attempt status;
- conservative fallback status;
- holdout-consumption rules;
- claims permitted;
- claims forbidden;
- privacy and publication controls.

## Deterministic builder rules

The builder must:

1. validate both source JSON files through strict Pydantic contracts;
2. verify their exact expected SHA-256 hashes;
3. verify cross-report candidate and holdout identities;
4. require `ranking_safety_regression`;
5. require `KEEP_DIAGNOSTIC_ONLY`;
6. require `closed_not_promoted`;
7. require conservative fallback status;
8. write canonical UTF-8 LF JSON and Markdown;
9. hash every generated release file;
10. write a sorted manifest last;
11. reject output overwrite unless explicit check mode confirms byte identity;
12. reject output paths outside the repository root.

## Required tests

### Contract tests

- unknown fields rejected;
- invalid validity marker rejected;
- positive promotion status rejected;
- missing conservative fallback rejected;
- missing ranking failure rejected.

### Source-integrity tests

- replay-report hash drift rejected;
- closeout-decision hash drift rejected;
- candidate identity mismatch rejected;
- holdout identity mismatch rejected;
- promotion state mismatch rejected.

### Sanitization tests

The generated pack must reject or exclude:

- raw prompt text;
- `.jsonl` records;
- `.zip` archives;
- API keys or tokens;
- environment-variable dumps;
- local absolute paths;
- raw logits;
- private, client, or customer markers;
- threshold-promotion or scheduler-promotion claims.

### Determinism tests

- repeated in-memory builds are identical;
- canonical report rebuild is byte-identical;
- manifest entry ordering is stable;
- file hashes and byte counts match;
- Windows and POSIX path rendering uses repository-relative POSIX paths.

### Claim-boundary tests

The pack must visibly state:

```text
candidate_not_promoted=true
threshold_promotion_authorized=false
scheduler_promotion_authorized=false
production_claim_authorized=false
```

The pack must not state or imply:

```text
candidate passed
scheduler utility improved
production speedup proven
production latency reduced
production cost savings proven
serving readiness established
```

## Privacy and security controls

- Aggregate retained metrics only.
- No raw prompt text.
- No private or customer data.
- No secrets or credentials.
- No raw logs or environment dumps.
- No user-input collection.
- No live inference.
- Local deterministic generation only.

## Publication-readiness gate

Building the local pack does not publish it.

Actual publication requires a later explicit decision covering:

- license selection;
- final hash review;
- dataset card review;
- evidence-boundary prominence;
- platform repository naming;
- visibility setting;
- no-secret confirmation;
- no live inference;
- rollback or unpublish procedure.

## Acceptance criteria

The implementation slice passes only if:

```text
source_integrity_passed=true
canonical_build_passed=true
sanitization_passed=true
claims_boundary_passed=true
validity_marker=CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY
publication_status=local_pack_only
```

## Non-claims

This plan does not:

- publish to Hugging Face;
- select a license;
- promote the candidate calibrator;
- promote a threshold or scheduler;
- establish adaptive-policy utility from Kaggle evidence;
- establish production speed, latency, throughput, cost, or serving readiness;
- authorize a new calibrator programme.

## Next slice after this plan

Implement and retain the deterministic local bounded negative-evidence release pack.
