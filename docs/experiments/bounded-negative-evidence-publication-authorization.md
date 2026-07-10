# Bounded Negative-Evidence Publication Authorization

## Result

The exact local Hugging Face Dataset candidate is authorized for a later controlled upload.

```text
decision_outcome=AUTHORIZE_EXACT_PUBLICATION
publication_authorized=true
publication_performed=false
source_commit=489ebb5
```

## Authorized candidate

```text
candidate_id=specsafe-bounded-negative-evidence-hf-candidate-v1
repository_type=dataset
repository_name=specsafe-bounded-negative-evidence-v1
visibility=public
gated=false
validity_marker=CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY
```

## Exact manifest boundary

```text
publication_manifest_sha256=6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6
publication_manifest_byte_count=4135
```

The authorization covers only the nine committed candidate files and is revoked automatically by
any candidate-byte drift.

## Gate result

```text
candidate_manifest_hash_verified=true
candidate_manifest_schema_valid=true
candidate_entries_verified=true
candidate_file_allowlist_passed=true
final_sanitization_passed=true
negative_evidence_boundary_retained=true
license_scope_bounded=true
rollback_controls_present=true
no_credentials_present=true
remote_repository_created=false
public_upload_performed=false
```

## Next gate

Perform one controlled Hugging Face Dataset publication, then retain and verify a remote receipt
covering the namespace, repository URL, revision, exact file hashes, visibility, and metadata.
