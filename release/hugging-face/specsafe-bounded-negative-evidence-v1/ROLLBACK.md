# Rollback and Unpublish Runbook

## Current state

```text
publication_status=local_candidate_upload_not_authorized
public_upload_authorized=false
```

No remote repository is created or modified by this candidate builder.

## Pre-publication stop

Before any upload, rerun the canonical candidate check and obtain an explicit publication-authorization decision tied to the exact `publication_manifest.json` SHA-256. Stop if any byte, claim, license scope, or sanitization result differs.

## Unpublish procedure after a future authorized release

1. Disable public access or remove the Hugging Face Dataset repository through the repository settings.
2. Record the repository URL, last published revision, publication-manifest SHA-256, reason, actor, and timestamp in a local incident note.
3. Confirm that anonymous access no longer returns the publication candidate.
4. Preserve the canonical local candidate and governance evidence; do not rewrite the consumed holdout result.
5. Revoke or rotate publishing credentials if exposure, compromise, or unauthorized use is suspected.
6. Correct the local source or governance decision before considering a new publication candidate.

## Rollback triggers

- source hash or publication-manifest drift;
- missing negative-evidence or non-promotion labels;
- license-scope error;
- secret, local-path, private-data, raw-trace, archive, or model-payload exposure;
- unsupported positive, scheduler, or production claim;
- upload performed without explicit authorization.

Unpublishing limits future access but cannot revoke copies already obtained under CC BY 4.0.
