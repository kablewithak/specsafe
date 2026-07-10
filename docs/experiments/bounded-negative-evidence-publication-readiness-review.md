# Bounded Negative-Evidence Publication-Readiness Review

## Review target

```text
source_commit=60755d1
release_id=specsafe-bounded-negative-evidence-v1
release_directory=release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1
release_manifest_sha256=10b02b3a67c726c321d5f20b4350c75925e6bca1485575181b4eee9b70243f3b
release_manifest_byte_count=975
```

## Exact reviewed files

| File | Bytes | SHA-256 |
|---|---:|---|
| `README.md` | 3008 | `79906e66d11eb3d5c2c396167a441be669e6105b47edd335f0325a0815c8689f` |
| `evidence_boundary.md` | 1577 | `8053d6c01a816280847b79d8bc036f14733dd7bc2d12f27bedf35934ef166967` |
| `release_summary.json` | 4470 | `264886c6bb6d2490bb95b43a29506b04437972e5a42c6688db7dc7d124f8df90` |

The manifest itself is excluded from its own entry list and is reviewed separately by exact hash and
byte count.

## Retained evidence result

```text
validity_marker=CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY
candidate_not_promoted=true
ranking_safety_passed=false
promotion_attempt_status=closed_not_promoted
conservative_fallback_required=true
```

The release communicates a rejected candidate, not a successful calibration or scheduler result.

## Gate results

```text
release_manifest_hash_verified=true
release_manifest_schema_valid=true
release_entries_verified=true
release_summary_schema_valid=true
release_identity_alignment_passed=true
exact_file_allowlist_passed=true
sanitization_retained=true
claims_boundary_retained=true
validity_marker_prominent=true
non_promotion_prominent=true
license_selected=true
license_scope_bounded=true
hub_metadata_draft_prepared=true
rollback_plan_required=true
public_upload_performed=false
```

## License decision

```text
license_identifier=cc-by-4.0
license_name=Creative Commons Attribution 4.0 International
license_scope=sanitized_release_pack_original_materials_only
license_selection_status=selected_for_publication_candidate
licensor=Kabo Molefe
```

Excluded from this license decision:

- SpecSafe source code;
- retained Kaggle archives;
- raw trace or prompt records;
- the candidate calibrator artifact; and
- upstream models and their outputs.

## Hugging Face draft

```text
repository_type=dataset
repository_name=specsafe-bounded-negative-evidence-v1
visibility=public
gated=false
live_inference=false
user_input_collection=false
card_metadata_status=prepared_not_applied
```

The reviewed local release pack is intentionally not modified in this slice. YAML metadata, license,
attribution, and rollback files belong to the derived publication candidate.

## Decision

```text
decision_outcome=READY_FOR_PUBLICATION_CANDIDATE_ASSEMBLY
publication_status=review_passed_upload_not_authorized
publication_candidate_assembly_authorized=true
public_upload_authorized=false
```

## Reproduction

```powershell
python .\scripts\review_bounded_negative_evidence_publication.py --check
```

## Next gate

Build an exact local Hugging Face Dataset publication candidate with reviewed metadata, license,
attribution, publication manifest, rollback instructions, and no upload.
