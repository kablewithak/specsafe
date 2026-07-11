# Apply Manifest

## Slice

```text
branch=feat/hugging-face-space-prebuilt-candidate
commit_message=feat: freeze prebuilt hugging face space candidate
base_commit=ed5467a
remote_mutation=false
existing_private_space_mutation=false
```

## Add

```text
src/specsafe/hugging_face_space_prebuilt_candidate/__init__.py
src/specsafe/hugging_face_space_prebuilt_candidate/models.py
src/specsafe/hugging_face_space_prebuilt_candidate/builder.py
scripts/build_hugging_face_space_prebuilt_candidate.py
tests/test_hugging_face_space_prebuilt_candidate.py
docs/adr/ADR-0052-freeze-prebuilt-static-space-candidate.md
docs/experiments/hugging-face-space-prebuilt-candidate-result.md
docs/runbooks/hugging-face-space-prebuilt-candidate.md
release/hugging-face-space-prebuilt-publication/specsafe-reliability-lab/candidate/space/
release/hugging-face-space-prebuilt-publication/specsafe-reliability-lab/prebuilt_candidate_manifest.json
```

## Replace

```text
APPLY_MANIFEST.md
```

## Source boundary

```text
source_candidate_root=release/hugging-face-space-publication/specsafe-reliability-lab/candidate/space
source_candidate_manifest=release/hugging-face-space-publication/specsafe-reliability-lab/publication_candidate_manifest.json
source_candidate_file_count=35
source_candidate_tree_sha256=041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb
```

## Prebuilt boundary

```text
candidate_root=release/hugging-face-space-prebuilt-publication/specsafe-reliability-lab/candidate/space
candidate_manifest=release/hugging-face-space-prebuilt-publication/specsafe-reliability-lab/prebuilt_candidate_manifest.json
sdk=static
app_file=index.html
app_build_command=absent
provider_side_build_required=false
remote_mutation=false
next_authorized_step=rebind_controlled_publication_executor_to_prebuilt_candidate
```

## Generate

```powershell
python .\scripts\build_hugging_face_space_publication_candidate.py --check
python .\scripts\build_hugging_face_space_prebuilt_candidate.py --write
git status
```

## Validation

```powershell
python .\scripts\build_hugging_face_space_prebuilt_candidate.py --check
python -m pytest .\tests\test_hugging_face_space_prebuilt_candidate.py
python -m pytest
python -m ruff check .
python -m ruff format --check `
    .\src\specsafe\hugging_face_space_prebuilt_candidate `
    .\scripts\build_hugging_face_space_prebuilt_candidate.py `
    .\tests\test_hugging_face_space_prebuilt_candidate.py
git diff --check
git status
```

## Windows npm resolution repair

```text
observed_failure=windows_createprocess_could_not_resolve_unqualified_npm
windows_resolution_order=npm.cmd_then_npm
non_windows_resolution_order=npm
fully_qualified_executable_path=true
shell_invocation=false
missing_executable_error=typed_and_actionable
remote_mutation=false
credential_present=false
```
