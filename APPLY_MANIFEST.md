# Apply Manifest

## Slice

```text
branch=fix/hugging-face-space-static-scaffold
commit_message=fix: normalize hugging face static space scaffold
base_commit=e8e80e0
actual_space_publication=false
remote_mutation=false
```

## Add

```text
tests/test_hugging_face_space_hub_adapter.py
```

## Replace

```text
APPLY_MANIFEST.md
docs/runbooks/hugging-face-space-publication.md
src/specsafe/hugging_face_space_publication/hub_adapter.py
```

## Failure evidence

```text
remote_preflight=passed
private_space_creation=passed
publication_failure=remote_initial_state_invalid
provider_static_scaffold=.gitattributes,README.md,index.html,style.css
rollback_boundary=before_public_release
```

## Corrected provider boundary

```text
known_static_scaffold_allowlist=.gitattributes,README.md,index.html,style.css
known_scaffold_subset_allowed=true
unknown_initial_file_rejected=true
candidate_paths_overwritten=README.md,index.html
stale_scaffold_deleted=.gitattributes,style.css
post_commit_exact_file_count=35
post_commit_hash_verification=required
```

## Tooling-slice boundary

```text
remote_repository_created=false
remote_files_uploaded=false
publication_receipt_written=false
publication_allowed_from_feature_branch=false
next_authorized_step=merge_fix_then_publish_from_clean_main
```

## Validation

```powershell
python .\scripts\publish_hugging_face_space.py --check-local
python -m pytest .\tests\test_hugging_face_space_hub_adapter.py
python -m pytest .\tests\test_hugging_face_space_publication.py
python -m pytest .\tests\test_hugging_face_space_publication_git_gate.py
python -m pytest
python -m ruff check .
python -m ruff format --check `
    .\src\specsafe\hugging_face_space_publication\hub_adapter.py `
    .\tests\test_hugging_face_space_hub_adapter.py
git diff --check
git status
```
