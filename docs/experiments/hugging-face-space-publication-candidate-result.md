# Hugging Face Space Publication Candidate Result

## Result

```text
status=publication_candidate_frozen_locally
source_commit=2848e80
space_repository_name=specsafe-reliability-lab
actual_space_publication=false
remote_mutation=false
next_authorized_step=controlled_remote_space_creation_and_upload
```

The exact candidate is generated under:

```text
release/hugging-face-space-publication/specsafe-reliability-lab/candidate/space
```

The machine-readable manifest is retained at:

```text
release/hugging-face-space-publication/specsafe-reliability-lab/publication_candidate_manifest.json
```

The candidate output is stored outside the frozen evidence directory so the
existing two-file evidence allowlist remains canonical and independently
verifiable.

The manifest is the source of truth for:

- exact candidate file count;
- every relative path;
- every file byte count and SHA-256;
- aggregate candidate-tree SHA-256;
- frozen evidence identity;
- Space metadata;
- authorization and next-step boundaries.

## Preserved evidence

```text
evidence_index_byte_count=9206
evidence_index_sha256=de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e
decision=KEEP_DIAGNOSTIC_ONLY
failure_label=ranking_safety_regression
```

## Controls

The candidate:

- uses a public npm registry only;
- verifies the evidence before development or production build;
- fails if the evidence byte count, SHA-256, or read-only authorization changes;
- contains no backend, live inference, user-input route, analytics, token, or
  deployment credential;
- is checked against an exact file allowlist;
- is validated from a disposable copy so `node_modules`, `dist`, and browser
  output never enter the committed upload set;
- has not been uploaded to Hugging Face.

## Validation boundary

The committed candidate must pass:

```text
deterministic builder check
focused Python tests
full Python suite
Ruff lint and changed-file format checks
npm ci from a disposable candidate copy
npm audit
evidence check
ESLint
unit tests
production build
Playwright desktop/mobile smoke tests
manual desktop/mobile review
git diff check
```

Passing these gates proves a locally validated, deterministic publication
candidate. It does not prove successful remote build, public availability, or
anonymous access.
