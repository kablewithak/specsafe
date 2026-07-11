# Hugging Face Space Publication Candidate Runbook

## Purpose

Build and validate the exact standalone Space repository candidate without
creating or mutating a remote Hugging Face repository.

## Immutable candidate boundary

The committed candidate directory is an exact upload set, not a development
workspace. It must never retain `node_modules`, `dist`, Playwright reports, or
test-result output. All npm, build, browser, and manual visual gates run from a
disposable copy outside the repository.

```text
committed_candidate_mutation=false
validation_workspace=disposable_copy
```

## Build the candidate

From the SpecSafe repository root:

```powershell
python .\scripts\build_hugging_face_space_publication_candidate.py --write
git status
```

The publication candidate uses a separate release namespace. Do not place it
inside `release/hugging-face-space/specsafe-reliability-lab`, because that
frozen evidence directory permits exactly two files and no nested content.

The builder replaces only:

```text
release/hugging-face-space-publication/specsafe-reliability-lab/candidate/space
release/hugging-face-space-publication/specsafe-reliability-lab/publication_candidate_manifest.json
```

Running `--write` is also the deterministic recovery path if local runtime
artifacts were accidentally created inside the committed candidate directory. The
builder writes a complete sibling staging tree first, rotates the old candidate to
an external trash directory beside the repository, and swaps the clean candidate
into place without recursively deleting the npm tree. Trash cleanup is best effort
and cannot block the canonical candidate write. The exact candidate allowlist is
never relaxed.

```text
candidate_recursive_deletion=false
candidate_rotation_target=<repository-parent>/.specsafe-publication-candidate-trash
failed_trash_cleanup_blocks_candidate_write=false
```

## Verify deterministic output

```powershell
python .\scripts\build_hugging_face_space_publication_candidate.py --check
python -m pytest .\tests\test_hugging_face_space_publication_candidate.py
```

## Create a disposable validation workspace

```powershell
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
```

## Validate the standalone candidate copy

```powershell
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
```

The committed candidate lockfile must contain no internal registry reference:

```powershell
Select-String `
    -Path "$CandidateRoot\package-lock.json" `
    -Pattern "applied-caas-gateway|internal\.api\.openai\.org"
```

Expected result: no output.

## Manual visual review

Use the same disposable validation workspace:

```powershell
Push-Location $ValidationRoot
npm run dev
```

Open the Vite URL and review desktop and narrow mobile widths. Confirm:

- Question, Method, and Answer establish the north star;
- neutral outcomes are explicit;
- `MPC5-103` remains the loss;
- `MPC5-104` and `MPC5-105` remain the clearest wins;
- `KEEP_DIAGNOSTIC_ONLY`, `ranking_safety_regression`, and the approximately
  `24.36x` breach remain visible;
- no horizontal overflow exists;
- no global-winner or production-performance claim appears.

Stop the server with `Ctrl+C`, then clean the disposable workspace:

```powershell
Pop-Location
Remove-Item -LiteralPath $ValidationRoot -Recurse -Force

python .\scripts\build_hugging_face_space_publication_candidate.py --check
git status
```

The final candidate check proves that validation did not mutate the committed
upload set.

## Publication boundary

Stop after local validation and merge.

Do not:

- create a Hugging Face Space;
- create or use a write token;
- upload files;
- add a backend;
- enable OAuth;
- add analytics or user-input collection.

Remote creation and upload require a separate controlled slice.
