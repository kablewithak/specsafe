# Apply Manifest

## Slice

```text
branch=feat/hugging-face-dataset-publication-receipt
commit_message=feat: retain hugging face dataset publication receipt
actual_publication=false
```

## Add

```text
evidence/publication-receipts/specsafe-bounded-negative-evidence-v1/hugging_face_dataset_publication_receipt.json
src/specsafe/hugging_face_dataset_publication/receipt_verification.py
scripts/verify_hugging_face_dataset_publication_receipt.py
tests/test_hugging_face_dataset_publication_receipt.py
docs/adr/ADR-0048-retain-hugging-face-dataset-publication-receipt.md
docs/experiments/hugging-face-dataset-publication-result.md
```

## Replace

```text
src/specsafe/hugging_face_dataset_publication/__init__.py
docs/runbooks/hugging-face-dataset-publication.md
APPLY_MANIFEST.md
```

## Publication identity

```text
workflow_run_id=29128634332
repository_id=KaboKableMolefe/specsafe-bounded-negative-evidence-v1
published_revision=1ff151fc0646102f6e7b107d1bceb9a18e50098a
receipt_sha256=a63cd76cefa376fc4baa108f4d0fa06b66ed2c4561cea29f3ac2280837e525b7
receipt_byte_count=2834
remote_file_count=9
visibility=public
gated=false
actual_publication=false
```

## Validation

```powershell
python .\scripts\verify_hugging_face_dataset_publication_receipt.py --check
python -m pytest .\tests\test_hugging_face_dataset_publication_receipt.py
python -m pytest .\tests\test_hugging_face_dataset_publication.py
python -m pytest
python -m ruff check .
python -m ruff format --check .\src\specsafe\hugging_face_dataset_publication .\scripts\verify_hugging_face_dataset_publication_receipt.py .\tests\test_hugging_face_dataset_publication_receipt.py
git diff --check
```

## Next branch

```text
feat/hugging-face-space-evidence-index
```
