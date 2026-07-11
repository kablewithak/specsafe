# Apply Manifest — Hugging Face Space Publication Receipt Reconciliation

## Slice purpose

Retain the successful v2 Hugging Face Space publication receipt and reconcile it against the exact anonymous remote repository and application state.

## Frozen publication evidence

```text
repository_id=KaboKableMolefe/specsafe-reliability-lab
published_revision=453481cc16518ba8d8b425813aca4cfc74c2d0e8
published_from_git_sha=e456a7f1b8b8a1e3dddbbfc3a0f54ed3049f8b52
candidate_manifest_sha256=d377f18aa189cec1529b6385483059acecb675bdfc74eda767fc005e631f07e3
candidate_tree_sha256=4e1eb0f186ed629e2a2fa352cd8943da5a5771aa43198f51814bb5013cf71362
source_candidate_manifest_sha256=63a28d28416f67b55f62019ff6c5905c923de791564f8de8fa6859a676356b8d
source_candidate_tree_sha256=041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb
evidence_index_sha256=de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e
remote_file_count=5
provider_side_build_required=false
rollback_triggered=false
```

## Files supplied

```text
src/specsafe/hugging_face_space_publication_receipt/__init__.py
src/specsafe/hugging_face_space_publication_receipt/hub_adapter.py
src/specsafe/hugging_face_space_publication_receipt/models.py
src/specsafe/hugging_face_space_publication_receipt/service.py
scripts/verify_hugging_face_space_publication_receipt.py
tests/test_hugging_face_space_publication_receipt.py
tests/test_hugging_face_space_publication_receipt_hub_adapter.py
docs/adr/ADR-0054-retain-and-reconcile-space-publication-receipt.md
docs/experiments/hugging-face-space-publication-receipt-reconciliation-result.md
docs/runbooks/hugging-face-space-publication-receipt-verification.md
```

## Generated evidence

The remote reconciliation command writes:

```text
evidence/publication-receipts/specsafe-reliability-lab/
hugging_face_space_publication_reconciliation.json
```

The successful publication receipt already exists locally and must be staged with the generated reconciliation record:

```text
evidence/publication-receipts/specsafe-reliability-lab/
hugging_face_space_publication_receipt.json
```

## Boundaries

```text
remote_mutation=false
credential_used=false
anonymous_remote_verification=true
receipt_overwrite=false
reconciliation_overwrite=false
live_inference=false
user_input_collection=false
```
