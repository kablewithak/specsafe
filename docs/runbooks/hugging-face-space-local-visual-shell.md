# Hugging Face Space Local Visual Shell Runbook

## Purpose

Validate the local read-only Space interface and its story-and-clarity refinement without publishing or mutating any Hugging Face repository.

## Preconditions

```text
branch=feat/hugging-face-space-story-clarity
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
npm run test:e2e
Pop-Location
```

## Manual visual review

```powershell
Push-Location .\apps\specsafe-reliability-lab
npm run dev
```

Open the Vite URL. Keep this PowerShell session running during review. Stop the server with `Ctrl+C`, then run `Pop-Location`.

Review:

- the north star is understood before the detailed results;
- question, method, and answer form a coherent story;
- the outcome scoreboard gives wins, neutral cases, and losses equal visual weight;
- `MPC5-101`, `MPC5-102`, and `MPC5-106` are visibly neutral versus fixed length;
- the exact comparison matrix is easier to read than the removed grouped bar chart;
- visible `MPC5-103` loss;
- visible `MPC5-104` and `MPC5-105` wins;
- visible `KEEP_DIAGNOSTIC_ONLY` and `ranking_safety_regression`;
- visible `24.36x` breach;
- desktop and narrow mobile layouts remain deliberate;
- keyboard focus and tabs work;
- no horizontal overflow;
- no wording implies a global winner or production performance.

## Full repository gates

```powershell
python -m pytest
python -m ruff check .
git diff --check
git status
```

No Python file changes in this slice, so a Ruff formatting command over the legacy Python tree is not part of this gate.

## Publication boundary

Stop after local review and merge. Do not create an HF token, Space repository, or remote upload in this slice.
