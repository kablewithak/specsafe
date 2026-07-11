# Hugging Face Space Publication Receipt Reconciliation Result

## Baseline

The first source publication reached the provider boundary but failed in `CONFIG_ERROR` during provider-side build execution.

## Intervention

Publish locally validated prebuilt static assets with no provider-side build command.

## Observed publication result

```text
publication_status=passed
repository_id=KaboKableMolefe/specsafe-reliability-lab
published_revision=453481cc16518ba8d8b425813aca4cfc74c2d0e8
application_url=https://kabokablemolefe-specsafe-reliability-lab.static.hf.space
published_from_git_sha=e456a7f1b8b8a1e3dddbbfc3a0f54ed3049f8b52
private_stage_verified=true
anonymous_repository_verification_passed=true
anonymous_application_verification_passed=true
served_html_verified=true
static_build_ready=true
rollback_triggered=false
```

## Receipt boundary

```text
schema_version=specsafe_hugging_face_space_publication_receipt_v2
publication_id=specsafe-reliability-lab-hf-space-prebuilt-publication-v1
candidate_manifest_sha256=d377f18aa189cec1529b6385483059acecb675bdfc74eda767fc005e631f07e3
candidate_tree_sha256=4e1eb0f186ed629e2a2fa352cd8943da5a5771aa43198f51814bb5013cf71362
source_candidate_manifest_sha256=63a28d28416f67b55f62019ff6c5905c923de791564f8de8fa6859a676356b8d
source_candidate_tree_sha256=041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb
evidence_index_sha256=de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e
remote_file_count=5
provider_side_build_required=false
```

## Reconciliation gate

The generated reconciliation record must prove:

```text
anonymous_repository_verified=true
anonymous_file_hashes_verified=true
anonymous_application_verified=true
remote_public_and_ungated=true
remote_revision_matches_receipt=true
terminal_error_absent=true
credential_used=false
```

## Failure taxonomy

```text
hf_space_receipt_missing
hf_space_receipt_invalid
hf_space_receipt_secret_marker
hf_space_receipt_local_lineage_mismatch
hf_space_receipt_local_candidate_drift
hf_space_receipt_remote_repository_mismatch
hf_space_receipt_remote_file_drift
hf_space_receipt_remote_application_mismatch
hf_space_receipt_reconciliation_already_exists
hf_space_receipt_reconciliation_invalid
```

## Maturity statement

This is a production-shaped, anonymously reconciled static publication with retained exact evidence. It is not a claim of production uptime, scale, load tolerance, incident response, or customer-data validation.
