# ADR-0051: Controlled Hugging Face Space Publication

## Status

Accepted for implementation. Remote publication remains pending until this tooling is merged to `main`.

## Context

SpecSafe now retains an exact 35-file static-Space candidate with a fixed aggregate tree hash. The next risk is no longer frontend implementation. It is remote mutation: creating the correct Space, uploading only the authorized bytes, proving private-stage integrity, making the repository public, verifying anonymous access, and retaining a credential-free receipt.

Running ad hoc CLI uploads would weaken the evidence chain because `.gitignore` behavior, pre-existing remote files, accidental namespace selection, partial uploads, and missing rollback behavior would not be captured as deterministic gates.

## Decision

Add a local, typed publication executor that:

1. verifies the frozen candidate against its strict manifest and aggregate tree hash;
2. requires the exact `KaboKableMolefe/specsafe-reliability-lab` identity;
3. rejects an existing remote Space rather than overwriting it;
4. creates a private static Space;
5. commits the exact 35-file allowlist in one governed commit;
6. verifies every remote file byte-for-byte while private;
7. changes visibility to public;
8. repeats repository verification anonymously;
9. waits for the anonymous static application to return HTML with the expected shell markers;
10. writes a strict credential-free publication receipt;
11. deletes the new Space on private-stage failure or returns it to private on public-stage failure.

The executor may perform remote mutation only from a clean local `main` branch. The Hugging Face token is accepted only from the current process environment and is passed directly to `HfApi`; it is never printed, written to a receipt, or persisted by this workflow.

## Why the tooling merges before publication

Publication code must be reviewed, tested, and present on `main` before it can mutate the remote Hub. The tooling PR therefore performs no remote mutation. After merge, publication runs from clean `main`, and the generated receipt is committed in a separate receipt/reconciliation branch.

## Alternatives rejected

### `hf upload` from the candidate directory

Rejected because it does not make the complete allowlist, rollback, namespace, private-stage, anonymous verification, and receipt behavior explicit in one testable service boundary.

### Upload directly to a public Space

Rejected because a byte or metadata failure would be publicly visible before verification.

### Allow overwriting an existing Space

Rejected because the first publication must establish an unambiguous repository identity and revision. Updates require a separate, explicit policy.

### Persist a token with `hf auth login`

Rejected for this workflow. The token remains process-local and must be removed from the PowerShell environment after publication.

## Consequences

- The first remote publication is deterministic, inspectable, and rollback-aware.
- An existing Space with the same identity blocks publication instead of being modified.
- Public verification covers repository bytes and the served static application shell.
- Manual incognito review remains an acceptance gate before the receipt is committed.
- The tooling does not claim production serving validation; the Space is a static public case study.
