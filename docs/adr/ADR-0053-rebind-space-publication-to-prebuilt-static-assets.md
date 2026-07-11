# ADR-0053: Rebind Space Publication to Prebuilt Static Assets

## Status

Accepted for implementation.

## Context

The first controlled Space publication uploaded and privately verified the exact 35-file source
candidate, switched the repository public, then failed at the Hugging Face provider-side build
boundary with `CONFIG_ERROR`. The build-log endpoint returned HTTP 500. The executor returned the
Space to private and wrote no receipt.

A second immutable candidate now contains only the locally validated static runtime:

```text
source_candidate_file_count=35
source_candidate_tree_sha256=041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb
prebuilt_candidate_file_count=5
prebuilt_candidate_tree_sha256=4e1eb0f186ed629e2a2fa352cd8943da5a5771aa43198f51814bb5013cf71362
provider_side_build_required=false
```

## Decision

The controlled publication executor is rebound to the committed five-file prebuilt candidate.

The executor must:

1. validate the exact prebuilt manifest, source-candidate lineage, file paths, byte counts, file
   hashes, and aggregate tree hash;
2. reject any candidate that reintroduces `app_build_command`;
3. create a new private static Space only when the target repository is absent;
4. commit exactly the five prebuilt files;
5. verify the exact private repository state and hashes;
6. switch the Space public and repeat exact anonymous repository verification;
7. verify the anonymously served HTML;
8. write a versioned, sanitized receipt bound to the local Git SHA and both candidate trees;
9. delete a newly created Space on pre-publication failure, or return it to private after public
   release failure;
10. fail immediately when Hugging Face reports `BUILD_ERROR`, `RUNTIME_ERROR`, or `CONFIG_ERROR`.

The existing failed private Space is not mutated by this implementation slice. It is deleted only
after this executor is merged to clean `main`, immediately before the final preflight and governed
publication.

## Consequences

### Positive

- Serving no longer depends on Hugging Face executing npm.
- The published repository contains only runtime assets and frozen evidence.
- The receipt preserves lineage from the 35-file source candidate to the five-file runtime.
- Terminal provider errors trigger immediate rollback instead of consuming the full timeout.

### Trade-offs

- Generated asset filenames are immutable release inputs and require a new candidate when the local
  build changes.
- The failed private Space must be deliberately removed before final publication because the
  existing-repository policy remains `reject`.
- This proves a controlled static publication path, not production serving performance.
