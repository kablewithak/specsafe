# Hugging Face Dataset Publication Runbook

## Purpose

Publish the exact authorized SpecSafe negative-evidence Dataset and retain proof that the public remote bytes match the local candidate.

## Authorized target

```text
namespace=KaboKableMolefe
repository_name=specsafe-bounded-negative-evidence-v1
repository_id=KaboKableMolefe/specsafe-bounded-negative-evidence-v1
repository_type=dataset
visibility=public
gated=false
```

## Primary route: GitHub Actions

The workflow is:

```text
.github/workflows/publish-hugging-face-dataset.yml
```

It is manual only. It does not run on pushes or pull requests.

### One-time GitHub setup

In the SpecSafe GitHub repository:

1. Open **Settings**.
2. Open **Environments**.
3. Create an environment named `hugging-face-publication`.
4. Add an environment secret named `HF_TOKEN` containing a Hugging Face token with permission to create and update repositories under `KaboKableMolefe`.
5. Optionally enable required reviewers for the environment.

Do not add the token as a repository file, workflow input, command-line argument, issue comment, pull-request comment, or Actions output.

### Manual publication

After the workflow file is merged to `main`:

1. Open **Actions**.
2. Select **Publish Hugging Face Dataset**.
3. Choose **Run workflow**.
4. Keep the branch as `main`.
5. Keep the namespace exactly as `KaboKableMolefe`.
6. Enter the confirmation phrase exactly:

```text
PUBLISH_EXACT_DATASET
```

7. Run the workflow once.

The workflow performs a no-write remote preflight before publication. It rejects an existing target repository rather than overwriting unknown remote content.

### Successful result

A successful run publishes and anonymously verifies:

```text
https://huggingface.co/datasets/KaboKableMolefe/specsafe-bounded-negative-evidence-v1
```

It then uploads an Actions artifact named like:

```text
specsafe-hf-dataset-publication-receipt-<run-id>
```

The artifact contains:

```text
evidence/publication-receipts/specsafe-bounded-negative-evidence-v1/hugging_face_dataset_publication_receipt.json
```

Download the artifact for the next receipt-review and repository-reconciliation pull request. Do not rerun a successful publication because the controlled publisher intentionally rejects an existing Dataset.

## Local fallback

Use the local path only if GitHub Actions is unavailable and the locally authenticated Hugging Face account is exactly `KaboKableMolefe`.

### Local check

```powershell
python .\scripts\publish_hugging_face_dataset.py --check-local
```

### Remote preflight

```powershell
python .\scripts\publish_hugging_face_dataset.py `
  --preflight `
  --namespace KaboKableMolefe
```

### Controlled local publication

```powershell
python .\scripts\publish_hugging_face_dataset.py `
  --publish `
  --namespace KaboKableMolefe
```

The local route writes the receipt directly into the repository working tree. Review and commit it on a dedicated feature branch.

## Stop conditions

Stop and investigate if:

- authentication does not identify `KaboKableMolefe`;
- the target Dataset already exists before the first authorized publication;
- any local candidate byte has drifted;
- any unexpected remote file appears;
- any remote hash differs;
- the public repository remains private or gated;
- anonymous verification fails;
- the publication receipt already exists; or
- the workflow is not running from `main`.

Do not publish under another name or namespace merely to bypass a failed gate.
