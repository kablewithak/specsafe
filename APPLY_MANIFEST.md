# Apply Manifest

## Slice

```text
branch=feat/hugging-face-space-publication-candidate
commit_message=feat: freeze hugging face space publication candidate
source_commit=2848e80
actual_space_publication=false
remote_mutation=false
```

## Add

```text
src/specsafe/hugging_face_space_publication_candidate/__init__.py
src/specsafe/hugging_face_space_publication_candidate/models.py
src/specsafe/hugging_face_space_publication_candidate/builder.py
scripts/build_hugging_face_space_publication_candidate.py
tests/test_hugging_face_space_publication_candidate.py
docs/adr/ADR-0050-freeze-hugging-face-space-publication-candidate.md
docs/experiments/hugging-face-space-publication-candidate-result.md
docs/runbooks/hugging-face-space-publication-candidate.md
release/hugging-face-space-publication/specsafe-reliability-lab/candidate/space/
release/hugging-face-space-publication/specsafe-reliability-lab/publication_candidate_manifest.json
```

## Replace

```text
README.md
tests/test_hugging_face_space_evidence_index.py
APPLY_MANIFEST.md
```

## Namespace invariant

```text
frozen_evidence_root=release/hugging-face-space/specsafe-reliability-lab
publication_candidate_root=release/hugging-face-space-publication/specsafe-reliability-lab
publication_candidate_nested_in_evidence_root=false
```

## Validation workspace invariant

```text
committed_candidate_mutation=false
committed_candidate_runtime_artifacts=false
validation_workspace=$env:TEMP/specsafe-reliability-lab-validation
validation_workspace_disposable=true
candidate_replacement=staged_external_rotation
candidate_recursive_deletion=false
candidate_trash_root=<repository-parent>/.specsafe-publication-candidate-trash
failed_trash_cleanup_blocks_candidate_write=false
```

## Candidate contract

```text
space_repository_name=specsafe-reliability-lab
sdk=static
app_build_command=npm run build
app_file=dist/index.html
canonical_evidence_sha256=de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e
canonical_evidence_byte_count=9206
registry=https://registry.npmjs.org/
actual_space_publication=false
remote_mutation=false
next_authorized_step=controlled_remote_space_creation_and_upload
```

## Generate

```powershell
python .\scripts\build_hugging_face_space_publication_candidate.py --write
git status
```

## Validation

```powershell
python .\scripts\build_hugging_face_space_publication_candidate.py --check
python -m pytest .\tests\test_hugging_face_space_publication_candidate.py
python -m pytest .\tests\test_hugging_face_space_evidence_index.py

$CandidateRoot = (Resolve-Path `
    ".\release\hugging-face-space-publication\specsafe-reliability-lab\candidate\space"
).Path
$ValidationRoot = Join-Path $env:TEMP "specsafe-reliability-lab-validation"

Remove-Item -LiteralPath $ValidationRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $ValidationRoot | Out-Null

Get-ChildItem -LiteralPath $CandidateRoot -Force |
    ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $ValidationRoot -Recurse -Force
    }

Push-Location $ValidationRoot
npm ci
npm audit --audit-level=low
npm run evidence:check
npm run lint
npm run test
npm run build
npm run test:e2e:install
npm run test:e2e
Pop-Location

Remove-Item -LiteralPath $ValidationRoot -Recurse -Force

python .\scripts\build_hugging_face_space_publication_candidate.py --check
python -m pytest
python -m ruff check .
python -m ruff format --check `
    .\src\specsafe\hugging_face_space_publication_candidate `
    .\scripts\build_hugging_face_space_publication_candidate.py `
    .\tests\test_hugging_face_space_publication_candidate.py `
    .\tests\test_hugging_face_space_evidence_index.py
git diff --check
```
