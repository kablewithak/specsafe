# Hugging Face Space Publication Receipt Verification Runbook

## Local verification

No network action or credential is used.

```powershell
python .\scripts\verify_hugging_face_space_publication_receipt.py --check-local
```

The command validates the strict receipt contract, exact publication lineage, candidate manifests, local candidate bytes, file hashes, and aggregate candidate-tree hash.

## Anonymous remote reconciliation

The publication token must be absent.

```powershell
Test-Path Env:HF_TOKEN
```

Expected:

```text
False
```

Write the reconciliation evidence once:

```powershell
python .\scripts\verify_hugging_face_space_publication_receipt.py `
    --write-remote-reconciliation
```

The gateway explicitly uses anonymous Hugging Face reads and bounded retries for `429`, `500`, `502`, `503`, and `504` responses.

## Committed evidence verification

```powershell
python .\scripts\verify_hugging_face_space_publication_receipt.py --check-committed
```

This performs no network action. It proves the committed reconciliation remains canonically serialized and remains bound to the exact retained receipt.

## Required retained files

```text
evidence/publication-receipts/specsafe-reliability-lab/
hugging_face_space_publication_receipt.json

evidence/publication-receipts/specsafe-reliability-lab/
hugging_face_space_publication_reconciliation.json
```

## Manual browser review

Open the application in an incognito browser and verify:

- no authentication is required;
- the North Star appears before detailed results;
- neutral outcomes remain visible;
- `MPC5-103` remains the loss;
- `MPC5-104` and `MPC5-105` remain the clearest wins;
- `KEEP_DIAGNOSTIC_ONLY` remains visible;
- `ranking_safety_regression` and approximately `24.36x` remain visible;
- no prompt, upload, form, or input control exists;
- desktop and narrow-mobile views have no horizontal overflow.

## Failure behavior

- receipt or candidate drift blocks reconciliation;
- private, gated, wrong-revision, wrong-SDK, or terminal remote state blocks reconciliation;
- any remote file mismatch blocks reconciliation;
- an invalid application response blocks reconciliation;
- existing reconciliation evidence is never overwritten;
- no remote mutation exists in this workflow.
