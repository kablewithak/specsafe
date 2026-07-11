# ADR-0050: Freeze the Hugging Face Space Publication Candidate

## Status

Accepted.

## Context

The frozen Space evidence index, responsive local visual shell, browser smoke
tests, and story-and-clarity refinement are complete. The next public-proof
boundary is not remote publication. It is an exact standalone repository
candidate that can be reviewed, rebuilt, and hash-verified before any Hugging
Face credential or remote repository is used.

The source frontend lives inside the SpecSafe monorepo at:

```text
apps/specsafe-reliability-lab
```

That directory is suitable for local development, but it contains a monorepo
evidence-sync command. A standalone Space must instead contain the exact frozen
evidence file and verify it locally without reaching back into the SpecSafe
repository.

Hugging Face static Spaces use repository-root README YAML metadata. React
projects can declare `sdk: static`, run `npm run build`, and serve
`dist/index.html`.

## Decision

Create a deterministic publication-candidate builder with these boundaries:

```text
source_commit=2848e80
space_repository_name=specsafe-reliability-lab
candidate_root=release/hugging-face-space-publication/specsafe-reliability-lab/candidate/space
manifest=release/hugging-face-space-publication/specsafe-reliability-lab/publication_candidate_manifest.json
actual_space_publication=false
remote_mutation=false
```

The publication namespace is deliberately separate from the frozen evidence
directory. The evidence directory has a strict two-file allowlist for
`evidence_index.json` and `evidence_manifest.json`; nesting candidate output
there would invalidate the canonical evidence gate.

The builder will:

1. Copy an explicit allowlist of frontend source, configuration, lockfile, and
   test files.
2. Generate the Space README with exact static-Space metadata.
3. Generate a public-registry `.npmrc`.
4. Replace monorepo evidence synchronization with a standalone SHA-256,
   byte-count, and authorization-boundary verifier.
5. Copy the canonical frozen evidence index byte-for-byte.
6. Reject internal package registries, missing inputs, evidence drift,
   unexpected candidate files, and committed-output drift.
7. Write a strict Pydantic manifest containing every candidate file's path,
   byte count, SHA-256, and an aggregate candidate-tree SHA-256.
8. Treat the committed candidate directory as immutable and run npm, build,
   browser, and manual-review gates from a disposable copy outside the repository.

## Metadata

```yaml
title: SpecSafe - When Should AI Spend More Compute?
emoji: 🛡️
colorFrom: yellow
colorTo: red
sdk: static
app_build_command: npm run build
app_file: dist/index.html
fullWidth: true
header: mini
short_description: AI reliability case study on adaptive verification.
datasets:
  - KaboKableMolefe/specsafe-bounded-negative-evidence-v1
pinned: false
```

## Evidence boundary

The candidate retains:

```text
evidence_index_byte_count=9206
evidence_index_sha256=de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e
live_inference=false
user_input_collection=false
```

The candidate may format and display the frozen contract. It may not fetch raw
research artifacts, run inference, accept user input, tune thresholds, mutate
evidence, add analytics, or claim production performance.

## Options considered

### Publish the monorepo app directory directly

Rejected. Its evidence-sync script depends on paths outside the standalone
Space repository and does not freeze the exact upload set.

### Manually copy files into a Space

Rejected. Manual copying weakens reproducibility, makes omissions difficult to
detect, and provides no exact rollback identity.

### Add a backend or Docker Space

Rejected. The product is a read-only evidence surface. A server adds runtime,
security, cost, and maintenance failure modes without product value.

### Deterministic static publication candidate

Accepted. It is the smallest maintainable path that preserves source evidence,
deployment metadata, exact file identity, and rollback.

## Consequences

Positive:

- the remote upload set becomes explicit and reviewable;
- local and remote builds use the same candidate root;
- evidence and package-registry drift fail closed;
- rollback can target one candidate-tree identity;
- no Hugging Face credential is required for this slice.

Costs:

- generated candidate files are intentionally duplicated from the app source;
- every source change requires rebuilding and reviewing the candidate;
- package installation and browser gates must run from a disposable copy of the
  standalone candidate so runtime artifacts cannot contaminate the committed
  upload set.

## Next gate

After this candidate is merged and locally validated:

```text
controlled remote Space creation and exact upload
-> anonymous public verification
-> retained publication receipt
-> credential cleanup
```

No remote action is authorized by this ADR alone.
