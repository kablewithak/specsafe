# ADR-0048: Retain the Hugging Face Dataset Publication Receipt

## Status

Accepted.

## Context

GitHub Actions run `29128634332` successfully published and anonymously verified the exact
SpecSafe bounded negative-evidence Dataset at:

```text
https://huggingface.co/datasets/KaboKableMolefe/specsafe-bounded-negative-evidence-v1
```

The workflow produced a machine-readable receipt after private-stage verification, public release,
and anonymous exact-byte verification.

## Decision

Retain the exact workflow receipt in the SpecSafe repository and bind it to:

```text
receipt_sha256=a63cd76cefa376fc4baa108f4d0fa06b66ed2c4561cea29f3ac2280837e525b7
receipt_byte_count=2834
published_revision=1ff151fc0646102f6e7b107d1bceb9a18e50098a
remote_file_count=9
visibility=public
gated=false
```

A deterministic verifier will validate the receipt schema, exact artifact hash, repository identity,
publication gates, remote file list, remote hashes, and alignment with the committed local candidate.

## Credential boundary

The retained receipt contains no token, authorization header, API key, secret value, or environment
credential. The GitHub environment secret remains outside repository history.

## Rerun boundary

The successful Dataset publication workflow must not be rerun. The controlled publisher rejects an
existing target repository, and the retained receipt closes the initial Dataset publication gate.

## Consequence

After this receipt is merged, Dataset publication is locally reconciled and the next implementation
slice may begin the read-only, visually polished Hugging Face Space evidence index and application.
