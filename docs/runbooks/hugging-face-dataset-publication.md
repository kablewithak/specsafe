# Hugging Face Dataset Publication Runbook

## Current status

The initial Dataset publication completed successfully through GitHub Actions run `29128634332`.

```text
repository_id=KaboKableMolefe/specsafe-bounded-negative-evidence-v1
repository_type=dataset
visibility=public
gated=false
published_revision=1ff151fc0646102f6e7b107d1bceb9a18e50098a
publication_status=published_verified_receipt_retained
```

Public repository:

```text
https://huggingface.co/datasets/KaboKableMolefe/specsafe-bounded-negative-evidence-v1
```

## Retained receipt

```text
evidence/publication-receipts/specsafe-bounded-negative-evidence-v1/hugging_face_dataset_publication_receipt.json
```

Canonical local check:

```powershell
python .\scripts\verify_hugging_face_dataset_publication_receipt.py --check
```

The check verifies the exact receipt hash, strict schema, public repository identity, published
revision, publication gates, nine-file allowlist, file hashes, and local-candidate alignment. It uses
no Hugging Face credential and performs no remote mutation.

## Do not rerun publication

Do not rerun `.github/workflows/publish-hugging-face-dataset.yml` for this release. The initial
publication is complete, and the controlled publisher intentionally rejects an existing target
repository.

A future correction requires a new governed publication candidate, new authorization, and a new
release identity. Do not overwrite or silently modify this retained release.

## Credential handling

The GitHub environment secret `HF_TOKEN` remains outside repository history. It may be revoked after
receipt retention if it is not needed for another explicitly authorized publication workflow.

Never add a token to a repository file, workflow input, command-line argument, issue, pull request,
log, screenshot, or chat message.

## Unpublish triggers

Return the Dataset to private visibility or remove it when any of these conditions are confirmed:

- public bytes differ from the retained receipt;
- the negative-evidence or non-promotion labels disappear;
- the license boundary is incorrect;
- private data, credentials, raw prompts, traces, or model payloads are exposed;
- publication occurred outside the authorized namespace or target; or
- an unsupported promotion or production claim is introduced.

Record the repository URL, published revision, publication-manifest SHA-256, reason, actor, and time
before unpublishing. Rotate credentials if compromise or unauthorized use is suspected.

## Next phase

The next phase is a separate read-only Hugging Face Space. It will present the evidence as a polished,
mobile-friendly visual case study without changing the Dataset, collecting user data, or running live
model inference.
