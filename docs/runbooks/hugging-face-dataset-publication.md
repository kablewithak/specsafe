# Hugging Face Dataset Publication Runbook

## Purpose

Publish the exact authorized SpecSafe negative-evidence Dataset and retain proof that the public remote bytes match the local candidate.

## Local check

```powershell
python .\scripts\publish_hugging_face_dataset.py --check-local
```

This performs no network action.

## Authentication

Use the Hugging Face CLI login flow. Do not paste a token into a command, script argument, commit, log, screenshot, or chat message.

```powershell
hf auth login
```

## Remote preflight

Run preflight with the exact account or organization namespace selected for publication:

```powershell
python .\scripts\publish_hugging_face_dataset.py `
  --preflight `
  --namespace YOUR_HUGGING_FACE_NAMESPACE
```

Preflight confirms the authenticated namespace and rejects an existing repository. It creates or modifies nothing remotely.

## Controlled publication

```powershell
python .\scripts\publish_hugging_face_dataset.py `
  --publish `
  --namespace YOUR_HUGGING_FACE_NAMESPACE
```

The publisher stages privately, verifies exact bytes, releases publicly, verifies anonymously, and writes:

```text
evidence/publication-receipts/specsafe-bounded-negative-evidence-v1/hugging_face_dataset_publication_receipt.json
```

## Stop conditions

Stop and investigate if:

- authentication does not identify the intended owner;
- the target repository already exists;
- any local candidate byte has drifted;
- any unexpected remote file appears;
- any remote hash differs;
- the public repository is private or gated;
- anonymous verification fails;
- the receipt already exists.

Do not rerun publication against another namespace merely to bypass a failed gate.
