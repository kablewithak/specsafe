# Hugging Face Space prebuilt candidate runbook

## Boundary

This runbook does not mutate Hugging Face.

It converts the frozen 35-file source publication candidate into a locally
compiled static runtime candidate after the provider-side build entered
`CONFIG_ERROR`.

```text
source_candidate_tree_sha256=041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb
source_candidate_file_count=35
provider_side_build_required=false
remote_mutation=false
```

## Build

```powershell
python .\scripts\build_hugging_face_space_publication_candidate.py --check

python .\scripts\build_hugging_face_space_prebuilt_candidate.py --write

git status
```

The builder uses a disposable directory and runs:

```text
npm ci
npm run evidence:check
npm run lint
npm run test
npm run build
```

`HF_TOKEN` and known Hugging Face token environment variables are removed from
the child build environment.

## Validate

```powershell
python .\scripts\build_hugging_face_space_prebuilt_candidate.py --check

python -m pytest .\tests\test_hugging_face_space_prebuilt_candidate.py

python -m ruff check .

python -m ruff format --check `
    .\src\specsafe\hugging_face_space_prebuilt_candidate `
    .\scripts\build_hugging_face_space_prebuilt_candidate.py `
    .\tests\test_hugging_face_space_prebuilt_candidate.py

git diff --check
git status
```

## Expected runtime candidate

The exact asset names are build-derived and retained in
`prebuilt_candidate_manifest.json`. The candidate must contain:

```text
README.md
index.html
evidence/evidence_index.json
one or more compiled assets
```

The root README must contain:

```yaml
sdk: static
app_file: index.html
```

It must not contain `app_build_command`.

## Publication hold

Do not delete, modify, restart, or publish the existing private Space during
this slice. Remote publication remains blocked until a later slice binds the
controlled executor to the committed prebuilt manifest and exact aggregate tree
hash.
