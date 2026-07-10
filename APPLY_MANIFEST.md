# Apply Manifest

## Slice

```text
branch=feat/hugging-face-space-evidence-index
commit_message=feat: freeze hugging face space evidence index
actual_space_publication=false
```

## Add

```text
src/specsafe/hugging_face_space_evidence/__init__.py
src/specsafe/hugging_face_space_evidence/models.py
src/specsafe/hugging_face_space_evidence/builder.py
scripts/build_hugging_face_space_evidence_index.py
tests/test_hugging_face_space_evidence_index.py
release/hugging-face-space/specsafe-reliability-lab/evidence_index.json
release/hugging-face-space/specsafe-reliability-lab/evidence_manifest.json
docs/adr/ADR-0049-freeze-hugging-face-space-evidence-index.md
docs/experiments/hugging-face-space-evidence-index-result.md
```

## Replace

```text
tests/test_hugging_face_dataset_publication_receipt.py
APPLY_MANIFEST.md
```

## Frozen output

```text
space_repository_name=specsafe-reliability-lab
evidence_index_sha256=de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e
evidence_index_byte_count=9206
ui_implementation_started=false
actual_space_publication=false
```

## Source evidence

```text
controlled_synthetic_comparison_sha256=e82e21853526e687b068cd8a0b3abb4bb390da755be977bf5f3045148a7d17f4
bounded_negative_evidence_summary_sha256=264886c6bb6d2490bb95b43a29506b04437972e5a42c6688db7dc7d124f8df90
dataset_publication_receipt_sha256=a63cd76cefa376fc4baa108f4d0fa06b66ed2c4561cea29f3ac2280837e525b7
```

## Validation

```powershell
python .\scripts\build_hugging_face_space_evidence_index.py --check
python -m json.tool .\release\hugging-face-space\specsafe-reliability-lab\evidence_index.json | Out-Null
python -m json.tool .\release\hugging-face-space\specsafe-reliability-lab\evidence_manifest.json | Out-Null
python -m pytest .\tests\test_hugging_face_space_evidence_index.py
python -m pytest .\tests\test_hugging_face_dataset_publication_receipt.py
python -m pytest
python -m ruff check .
python -m ruff format --check .\src\specsafe\hugging_face_space_evidence .\scripts\build_hugging_face_space_evidence_index.py .\tests\test_hugging_face_space_evidence_index.py .\tests\test_hugging_face_dataset_publication_receipt.py
git diff --check
```
