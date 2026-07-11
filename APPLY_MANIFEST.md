# Apply Manifest

## Slice

```text
branch=feat/hugging-face-space-publication-executor
commit_message=feat: add controlled hugging face space publication executor
base_commit=aa791ab
actual_space_publication=false
remote_mutation=false
```

## Add

```text
src/specsafe/hugging_face_space_publication/__init__.py
src/specsafe/hugging_face_space_publication/models.py
src/specsafe/hugging_face_space_publication/service.py
src/specsafe/hugging_face_space_publication/hub_adapter.py
src/specsafe/hugging_face_space_publication/git_gate.py
scripts/publish_hugging_face_space.py
tests/test_hugging_face_space_publication.py
tests/test_hugging_face_space_publication_git_gate.py
docs/adr/ADR-0051-controlled-hugging-face-space-publication.md
docs/runbooks/hugging-face-space-publication.md
```

## Replace

```text
APPLY_MANIFEST.md
```

## Publication contract

```text
repository_id=KaboKableMolefe/specsafe-reliability-lab
repository_type=space
sdk=static
candidate_file_count=35
candidate_tree_sha256=041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb
evidence_index_sha256=de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e
existing_repository_policy=reject
upload_mode=private_stage_exact_commit_public_release
credential_policy=environment_token_never_logged_or_persisted
```

## Tooling-slice boundary

```text
remote_repository_created=false
remote_files_uploaded=false
publication_receipt_written=false
publication_allowed_from_feature_branch=false
next_authorized_step=merge_tooling_then_publish_from_clean_main
```

## Validation

```powershell
python .\scripts\publish_hugging_face_space.py --check-local
python -m pytest .\tests\test_hugging_face_space_publication.py
python -m pytest .\tests\test_hugging_face_space_publication_git_gate.py
python -m pytest
python -m ruff check .
python -m ruff format --check `
    .\src\specsafe\hugging_face_space_publication `
    .\scripts\publish_hugging_face_space.py `
    .\tests\test_hugging_face_space_publication.py `
    .\tests\test_hugging_face_space_publication_git_gate.py
git diff --check
git status
```
