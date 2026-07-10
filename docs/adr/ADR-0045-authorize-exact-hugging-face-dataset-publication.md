# ADR-0045: Authorize Exact Hugging Face Dataset Publication

## Status

Accepted.

## Date

2026-07-10

## Context

The local Hugging Face Dataset publication candidate is committed at merge commit `489ebb5`.
Its exact publication-manifest identity is:

```text
sha256=6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6
byte_count=4135
```

The candidate contains nine allowlisted files. It passed the final sanitization review, retains the
negative-evidence and non-promotion boundaries, includes bounded CC BY 4.0 material, and has a
rollback and unpublish runbook.

## Decision

Authorize publication of the exact candidate bytes to one Hugging Face **Dataset** repository:

```text
repository_name=specsafe-bounded-negative-evidence-v1
visibility=public
gated=false
license=cc-by-4.0
authorization_scope=exact_candidate_bytes_only
```

The authenticated namespace must be confirmed during the publication step. Credentials must be
managed outside the repository and must never be logged or committed.

## Authorized files

```text
ATTRIBUTION.md
LICENSE.md
README.md
ROLLBACK.md
evidence_boundary.md
publication_manifest.json
release_summary.json
sanitization_report.json
source_release_manifest.json
```

No transformed, generated, additional, or omitted file is authorized.

## Current action boundary

This ADR authorizes a later controlled publication action. It does not create a remote repository,
upload a file, access a Hugging Face credential, or claim that publication already occurred.

```text
decision_outcome=AUTHORIZE_EXACT_PUBLICATION
publication_authorized=true
publication_performed=false
```

Any candidate-byte drift automatically revokes this authorization and requires a new review.

## Required publication receipt

The publication step must retain:

- repository ID and URL;
- authenticated namespace;
- published revision;
- exact publication-manifest SHA-256;
- remote file hashes;
- publication timestamp; and
- remote visibility and metadata verification.

## Blocked actions

- Uploading files outside the exact allowlist.
- Modifying candidate bytes during upload.
- Publishing to an unconfirmed namespace.
- Logging or committing Hugging Face credentials.
- Skipping remote hash and visibility verification.
- Presenting the calibrator, scheduler, or system as promoted or production-ready.

## Consequences

The next slice may create the Dataset repository, upload the exact candidate, and retain a remote
publication receipt. The visually polished Hugging Face Space remains a separate presentation
project after the Dataset publication is verified.
