# Hugging Face Space Local Visual Shell Runbook

## Purpose

Validate the local read-only Space interface without publishing or mutating any Hugging Face repository.

## Preconditions

```text
branch=feat/hugging-face-space-visual-shell
working_tree=contains_only_this_slice
node=>=20.19<25
npm=>=10
python_environment=existing SpecSafe .venv
```

## Evidence checks

```powershell
python .\scripts\build_hugging_face_space_evidence_index.py --check

Push-Location .\apps\specsafe-reliability-lab
npm ci
npm audit --audit-level=low
npm run evidence:check
Pop-Location
```

## Frontend gates

```powershell
Push-Location .\apps\specsafe-reliability-lab
npm run lint
npm run test
npm run build
npm run test:e2e:install
npm run test:e2e
Pop-Location
```

## Manual visual review

```powershell
Push-Location .\apps\specsafe-reliability-lab
npm run dev
Pop-Location
```

Review:

- desktop and narrow mobile widths;
- hero comprehension within roughly twenty seconds;
- visible `MPC5-103` loss;
- visible `MPC5-104` and `MPC5-105` wins;
- visible `KEEP_DIAGNOSTIC_ONLY` and `ranking_safety_regression`;
- visible `24.36x` breach;
- keyboard focus and tabs;
- no horizontal overflow;
- no wording that implies a global winner or production performance.

## Full repository gates

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .\src .\scripts .\tests

git diff --check
git status
```

## Publication boundary

Stop after local review and merge. Do not create an HF token, Space repository, or remote upload in this slice.
