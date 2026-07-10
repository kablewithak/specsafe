# Hugging Face Dataset Publication Result

## Result

The exact bounded negative-evidence Dataset was published successfully:

```text
repository_id=KaboKableMolefe/specsafe-bounded-negative-evidence-v1
repository_type=dataset
final_visibility=public
gated=false
published_revision=1ff151fc0646102f6e7b107d1bceb9a18e50098a
published_at=2026-07-10T22:46:44.611965Z
```

Public repository:

```text
https://huggingface.co/datasets/KaboKableMolefe/specsafe-bounded-negative-evidence-v1
```

## Verification result

```text
authenticated_namespace_verified=true
private_stage_verified=true
anonymous_public_verification_passed=true
negative_evidence_marker_verified=true
candidate_non_promotion_verified=true
license_metadata_verified=true
rollback_triggered=false
remote_file_count=9
```

The nine public file hashes match the exact authorized local candidate. The retained publication
manifest SHA-256 is:

```text
6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6
```

## Receipt identity

```text
relative_path=evidence/publication-receipts/specsafe-bounded-negative-evidence-v1/hugging_face_dataset_publication_receipt.json
byte_count=2834
sha256=a63cd76cefa376fc4baa108f4d0fa06b66ed2c4561cea29f3ac2280837e525b7
```

## Reproduction

```powershell
python .\scripts\verify_hugging_face_dataset_publication_receipt.py --check
```

This verifies the retained receipt and local candidate without using a Hugging Face credential or
changing the public Dataset.

## Next gate

Build the Hugging Face Space from a frozen, read-only evidence index derived from the verified public
Dataset and the existing controlled scheduler evidence. The Space remains a presentation layer and
must not mutate evidence or perform live inference.
