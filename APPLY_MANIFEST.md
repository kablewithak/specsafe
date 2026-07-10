# Apply Manifest

## Slice

```text
branch=feat/github-actions-hugging-face-publication
commit_message=feat: add manual hugging face publication workflow
actual_publication=false
```

## Add

```text
.github/workflows/publish-hugging-face-dataset.yml
src/specsafe/hugging_face_dataset_publication/workflow_gate.py
scripts/validate_hugging_face_publication_dispatch.py
tests/test_hugging_face_dataset_publication_workflow.py
docs/adr/ADR-0047-manual-github-actions-hugging-face-publication.md
```

## Replace

```text
src/specsafe/hugging_face_dataset_publication/__init__.py
docs/runbooks/hugging-face-dataset-publication.md
APPLY_MANIFEST.md
```

## Exact target

```text
namespace=KaboKableMolefe
repository_name=specsafe-bounded-negative-evidence-v1
repository_id=KaboKableMolefe/specsafe-bounded-negative-evidence-v1
workflow_trigger=manual_workflow_dispatch_only
protected_environment=hugging-face-publication
secret_name=HF_TOKEN
actual_publication=false
```

## Workflow boundary

```text
source_ref=refs/heads/main
confirmation=PUBLISH_EXACT_DATASET
permissions=contents_read_only
automatic_git_commit=false
automatic_git_push=false
receipt_retained_as_workflow_artifact=true
```

## Validation

```powershell
python -m pytest .\tests\test_hugging_face_dataset_publication_workflow.py
python -m pytest .\tests\test_hugging_face_dataset_publication.py
python -m pytest
python -m ruff check .
python -m ruff format --check .\src\specsafe\hugging_face_dataset_publication .\scripts\validate_hugging_face_publication_dispatch.py .\tests\test_hugging_face_dataset_publication_workflow.py
git diff --check
```
