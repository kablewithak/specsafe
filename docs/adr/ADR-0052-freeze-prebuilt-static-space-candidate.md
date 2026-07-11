# ADR-0052: Freeze a locally built static-Space publication candidate

## Status

Accepted.

## Context

The exact 35-file React source candidate was uploaded to a private Hugging Face
Space and passed private and anonymous repository-byte verification. Hugging
Face then entered `CONFIG_ERROR` while executing the provider-side static build.
The build-log endpoint returned HTTP 500, no publication receipt was written,
and rollback returned the Space to private.

The source candidate remains valid. The unreliable boundary is the provider-side
Node build job, not the evidence contract or React implementation.

## Decision

Build and validate the React application locally in a disposable workspace, then
freeze only the generated static runtime assets as a second publication
candidate.

The prebuilt candidate:

- is derived only from the frozen 35-file source candidate;
- runs `npm ci`, evidence validation, lint, unit tests, and the production build;
- strips Hugging Face credentials from the build environment;
- contains `README.md`, `index.html`, built assets, and the frozen evidence index;
- uses `sdk: static` and `app_file: index.html`;
- contains no `app_build_command`;
- rejects source maps, source trees, package manifests, test files, and linked content;
- retains exact per-file hashes and an aggregate tree hash;
- requires a separate executor-rebinding slice before any new remote mutation.

## Alternatives rejected

### Keep retrying the provider build

Rejected. The same inputs already produced `CONFIG_ERROR`, and the diagnostic
endpoint failed with HTTP 500. Repetition would add activity without better
evidence.

### Edit the private Space manually

Rejected. Manual mutation would bypass the exact-file publication harness and
break local-to-remote provenance.

### Convert to Gradio or Docker

Rejected. SpecSafe is a read-only static evidence interface. Adding a Python or
container runtime would increase operational scope without buyer or evidence value.

## Consequences

The committed runtime candidate becomes smaller and removes provider-side Node
installation and compilation from the serving boundary. The existing private
failed Space remains untouched until the prebuilt candidate and an exact
executor binding are both merged.
