# Apply Manifest

## Slice

```text
branch=feat/controlled-hugging-face-dataset-publisher
commit_message=feat: add controlled hugging face dataset publisher
actual_publication=false
```

## Add

```text
src/specsafe/hugging_face_dataset_publication/__init__.py
src/specsafe/hugging_face_dataset_publication/models.py
src/specsafe/hugging_face_dataset_publication/service.py
src/specsafe/hugging_face_dataset_publication/hub_adapter.py
scripts/publish_hugging_face_dataset.py
tests/test_hugging_face_dataset_publication.py
docs/adr/ADR-0046-controlled-hugging-face-dataset-publication.md
docs/runbooks/hugging-face-dataset-publication.md
```

## Replace

```text
pyproject.toml
APPLY_MANIFEST.md
```

## Governing authorization

```text
authorization_decision_sha256=bf96e015379f8ad955791c28b8ba75b123b3d748d2192943190b056eb5aadc46
authorization_decision_byte_count=4528
publication_manifest_sha256=6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6
exact_candidate_file_count=9
```

## Publisher behavior

```text
remote_existing_repository_policy=reject
stage_visibility=private
final_visibility=public
gated=false
private_exact_byte_verification=true
anonymous_exact_byte_verification=true
credential_logging=false
actual_publication=false
```

## Validation

```powershell
python -m pip install -e ".[dev,publish]"
python .\scripts\publish_hugging_face_dataset.py --check-local
python -m pytest .\tests\test_hugging_face_dataset_publication.py
python -m pytest .\tests\test_hugging_face_publication_authorization.py
python -m pytest .\tests\test_hugging_face_publication_candidate.py
python -m pytest
python -m ruff check .
python -m ruff format --check .\src\specsafe\hugging_face_dataset_publication .\scripts\publish_hugging_face_dataset.py .\tests\test_hugging_face_dataset_publication.py
git diff --check
```
