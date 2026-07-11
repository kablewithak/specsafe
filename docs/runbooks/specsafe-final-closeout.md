# SpecSafe Final Closeout Runbook

## Purpose

Use this runbook once, after the final acceptance files land and before committing the closeout
slice. It performs non-mutating verification only.

It must not:

- publish or republish the Dataset or Space;
- write a new remote reconciliation record;
- use a Hugging Face token;
- refit a calibrator;
- reuse the consumed holdout;
- change thresholds, policies, fixtures, or public evidence.

## Preconditions

```text
expected_branch=docs/final-prd-acceptance-closeout
expected_base=clean_main_at_or_after_ee202e0
expected_token_state=HF_TOKEN_absent
expected_change_class=documentation_only
```

## Closeout verification

Run from the repository root:

```powershell
Test-Path Env:HF_TOKEN

python .\scripts\verify_hugging_face_dataset_publication_receipt.py --check

python .\scripts\verify_hugging_face_space_publication_receipt.py --check-local

python .\scripts\verify_hugging_face_space_publication_receipt.py --check-committed

python -m pytest

python -m ruff check .

git diff --check

git status
```

Expected token result:

```text
False
```

Expected verification result:

```text
dataset_receipt_check=pass
space_local_receipt_check=pass
space_committed_reconciliation_check=pass
python_test_suite=pass
ruff_check=pass
git_diff_check=pass
```

`ruff format --check` is not required for this documentation-only slice because no Python file is
changed. Future slices that change Python must restore the repository's independent Ruff format
gate against the explicit changed Python paths.

## Evidence that must remain unchanged

```text
candidate_decision=KEEP_DIAGNOSTIC_ONLY
candidate_failure=ranking_safety_regression
candidate_promotion=closed_not_promoted
adaptive_vs_fixed=2_wins_3_neutral_1_loss
adaptive_vs_threshold=3_wins_2_neutral_1_loss
adaptive_loss=MPC5-103
clearest_adaptive_wins=MPC5-104_MPC5-105
```

Dataset identity:

```text
repository_id=KaboKableMolefe/specsafe-bounded-negative-evidence-v1
published_revision=1ff151fc0646102f6e7b107d1bceb9a18e50098a
remote_file_count=9
```

Space identity:

```text
repository_id=KaboKableMolefe/specsafe-reliability-lab
published_revision=453481cc16518ba8d8b425813aca4cfc74c2d0e8
remote_file_count=5
sdk=static
provider_side_build_required=false
```

## Prohibited command during routine closeout

Do not run:

```text
python .\scripts\verify_hugging_face_space_publication_receipt.py --write-remote-reconciliation
```

The committed reconciliation is immutable and already retained. Routine verification uses
`--check-local` and `--check-committed` only.

## Failure handling

| Failure | Action |
|---|---|
| `HF_TOKEN` is present | Remove it from the current process before continuing. Do not print its value. |
| Dataset receipt check fails | Stop. Inspect receipt or local candidate drift. Do not republish. |
| Space local check fails | Stop. Inspect receipt lineage or candidate drift. Do not mutate the remote Space. |
| Committed reconciliation check fails | Stop. Inspect canonical serialization or receipt binding. Do not overwrite evidence. |
| Pytest fails | Stop. Fix the smallest evidence-backed regression before commit. |
| Ruff fails | Stop. Fix only the reported issue; do not change research behavior. |
| `git diff --check` fails | Stop. Correct whitespace or patch-integrity errors before staging. |

## Closeout completion condition

The closeout is complete only after:

```text
final_non_mutating_gates=passed
closeout_PR=merged
main=clean
origin_main=synchronized
feature_branch_cleanup=done
latest_main_commit=verified
```

After that boundary, v1 engineering work is closed. Optional portfolio packaging may continue, but
it must not rewrite the retained research outcome or claim production readiness.
