# ADR-0054: Retain and Reconcile the Hugging Face Space Publication Receipt

## Status

Accepted for implementation.

## Context

The prebuilt static Space was published and verified successfully from clean `main`.

```text
repository_id=KaboKableMolefe/specsafe-reliability-lab
published_revision=453481cc16518ba8d8b425813aca4cfc74c2d0e8
published_from_git_sha=e456a7f1b8b8a1e3dddbbfc3a0f54ed3049f8b52
remote_file_count=5
provider_side_build_required=false
rollback_triggered=false
```

The executor wrote a sanitized v2 receipt. The receipt is strong publication evidence, but retaining the JSON alone is insufficient. We also need an executable reconciliation gate proving that the retained receipt, committed candidate, anonymous remote repository, and served application still agree.

## Decision

Add a strict receipt-verification and anonymous reconciliation harness.

The harness will:

1. validate the receipt through the existing strict v2 receipt model;
2. reject credential markers;
3. bind the receipt to the exact publication Git SHA, remote revision, URLs, candidate manifest hash, candidate tree hash, source-candidate lineage, and evidence hash;
4. verify the committed five-file candidate byte-for-byte;
5. query the remote Space anonymously with `token=False`;
6. require public, ungated, static, non-terminal remote state;
7. verify the exact five-file allowlist and every remote byte hash at the published revision;
8. verify the public application returns HTML containing the expected application markers;
9. write one canonical reconciliation record atomically;
10. refuse to overwrite the receipt or reconciliation evidence.

## Alternatives rejected

### Keep only the raw receipt

Rejected because the receipt would remain passive evidence without an executable replay boundary.

### Reuse an authenticated token for reconciliation

Rejected because the public-access claim must be proven anonymously and the temporary publication token has already been removed and revoked.

### Verify only the current application URL

Rejected because an HTTP 200 does not prove exact repository files, revision, evidence lineage, or absence of remote drift.

## Consequences

### Positive

- the publication becomes queryable and replayable evidence;
- anonymous access is tested separately from authenticated publication;
- local and remote drift receive explicit failure labels;
- future handovers can resume from a clean retained-publication boundary;
- the evidence package is commercially legible as a deployment/release reliability proof.

### Trade-offs

- remote reconciliation remains dependent on Hugging Face read endpoints;
- bounded retries reduce transient failure noise but cannot prove platform availability permanently;
- this evidence proves one successful static release, not production load, uptime, or operational ownership.

## Handover boundary

The nearest clean handover boundary is reached after:

1. the receipt and reconciliation PR is merged;
2. `main` is clean and synchronized;
3. local receipt verification passes;
4. committed reconciliation verification passes;
5. the published Space still passes anonymous desktop and narrow-mobile review.
