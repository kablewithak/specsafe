# Apply Manifest

## Slice

```text
branch=feat/hugging-face-space-prebuilt-publication-executor
commit_message=feat: bind space publication to prebuilt static assets
base_commit=ffab071
actual_space_publication=false
remote_mutation=false
```

## Add

```text
docs/adr/ADR-0053-rebind-space-publication-to-prebuilt-static-assets.md
docs/experiments/hugging-face-space-prebuilt-publication-executor-result.md
```

## Replace

```text
APPLY_MANIFEST.md
docs/runbooks/hugging-face-space-publication.md
scripts/publish_hugging_face_space.py
src/specsafe/hugging_face_space_publication/hub_adapter.py
src/specsafe/hugging_face_space_publication/models.py
src/specsafe/hugging_face_space_publication/service.py
tests/test_hugging_face_space_hub_adapter.py
tests/test_hugging_face_space_publication.py
```

## Publication contract

```text
repository_id=KaboKableMolefe/specsafe-reliability-lab
repository_type=space
sdk=static
app_file=index.html
app_build_command=absent
source_candidate_file_count=35
source_candidate_tree_sha256=041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb
candidate_file_count=5
candidate_tree_sha256=4e1eb0f186ed629e2a2fa352cd8943da5a5771aa43198f51814bb5013cf71362
evidence_index_sha256=de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e
provider_side_build_required=false
existing_repository_policy=reject
upload_mode=private_stage_exact_commit_public_release
confirmation=PUBLISH_EXACT_PREBUILT_SPACE
```

## Tooling-slice boundary

```text
failed_private_space_mutated=false
remote_repository_created=false
remote_files_uploaded=false
publication_receipt_written=false
publication_allowed_from_feature_branch=false
next_authorized_step=merge_executor_then_remove_failed_private_space_and_publish_from_clean_main
```

## Validation

```powershell
python .\scripts\build_hugging_face_space_prebuilt_candidate.py --check
python .\scripts\publish_hugging_face_space.py --check-local
python -m pytest .\tests\test_hugging_face_space_publication.py
python -m pytest .\tests\test_hugging_face_space_hub_adapter.py
python -m pytest .\tests\test_hugging_face_space_publication_git_gate.py
python -m pytest
python -m ruff check .
python -m ruff format --check `
    .\src\specsafe\hugging_face_space_publication `
    .\scripts\publish_hugging_face_space.py `
    .\tests\test_hugging_face_space_publication.py `
    .\tests\test_hugging_face_space_hub_adapter.py
git diff --check
git status
```
