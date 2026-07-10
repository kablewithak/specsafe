# Apply Manifest — Post-Closeout Repository Reconciliation

## Slice

```text
branch=docs/post-closeout-publication-route-reconciliation
commit=docs: reconcile post-closeout publication route
base_commit=54227a0
scope=docs-only
```

## Files

```text
README.md
docs/PRD_STATUS_RECONCILIATION_2026-07-10.md
docs/adr/ADR-0043-bounded-negative-evidence-publication-route.md
docs/experiments/bounded-negative-evidence-release-plan.md
APPLY_MANIFEST.md
```

## Purpose

- update stale repository status statements after the completed synthetic and Kaggle evidence work;
- preserve the governing PRD requirements while reconciling current phase facts;
- select bounded negative-evidence packaging as the next route;
- defer automatic calibrator redesign;
- define the local release-pack boundary before implementation;
- keep actual Hugging Face publication and license selection as later explicit gates.

## Validation

Docs-only validation:

```powershell
Test-Path ".\README.md"
Test-Path ".\docs\PRD_STATUS_RECONCILIATION_2026-07-10.md"
Test-Path ".\docs\adr\ADR-0043-bounded-negative-evidence-publication-route.md"
Test-Path ".\docs\experiments\bounded-negative-evidence-release-plan.md"
Test-Path ".\APPLY_MANIFEST.md"

git diff --check
```

## Next authorized branch

```text
feat/bounded-negative-evidence-release-pack
```
