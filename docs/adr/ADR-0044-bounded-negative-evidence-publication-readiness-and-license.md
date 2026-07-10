# ADR-0044: Select CC BY 4.0 and Authorize Publication-Candidate Assembly

## Status

Accepted.

## Date

2026-07-10

## Context

The deterministic bounded negative-evidence release pack is committed and canonical at merge commit
`60755d1`. Its exact manifest SHA-256 is:

```text
10b02b3a67c726c321d5f20b4350c75925e6bca1485575181b4eee9b70243f3b
```

The reviewed pack contains only:

- a dataset-card-style `README.md`;
- an evidence-boundary document;
- an aggregate machine-readable release summary; and
- a manifest covering the three pre-manifest files.

It contains no row-level dataset, raw prompts, raw traces, retained Kaggle archives, model payloads,
secrets, customer data, live inference, or user-input collection.

The release remains labelled:

```text
CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY
```

The candidate remains `KEEP_DIAGNOSTIC_ONLY`, `closed_not_promoted`, and unavailable for trusted
automated scheduling.

## Decision

Select **Creative Commons Attribution 4.0 International** using the Hugging Face identifier:

```text
cc-by-4.0
```

The selected license applies only to the original sanitized materials assembled into the bounded
negative-evidence publication candidate.

The license does not apply to:

- the SpecSafe source-code repository as a whole;
- retained Kaggle archives;
- raw trace or prompt records;
- the candidate calibrator artifact; or
- upstream models and their outputs.

The attribution notice will be:

```text
SpecSafe Bounded Negative-Evidence Release v1 © 2026 Kabo Molefe,
licensed under CC BY 4.0.
```

This is an engineering distribution choice, not legal advice.

## Publication-readiness result

The exact local release pack passes:

```text
release_manifest_hash_verified=true
release_entries_verified=true
release_summary_schema_valid=true
exact_file_allowlist_passed=true
sanitization_retained=true
claims_boundary_retained=true
validity_marker_prominent=true
non_promotion_prominent=true
license_selected=true
license_scope_bounded=true
```

The decision outcome is:

```text
decision_outcome=READY_FOR_PUBLICATION_CANDIDATE_ASSEMBLY
publication_candidate_assembly_authorized=true
public_upload_authorized=false
```

## Hugging Face metadata draft

The next slice may prepare a local Hugging Face Dataset repository candidate with:

```yaml
license: cc-by-4.0
pretty_name: SpecSafe Bounded Negative-Evidence Release v1
tags:
  - ai-reliability
  - calibration
  - evaluation
  - negative-results
  - governance
```

The target repository type is `dataset`. The release has no row-level dataset and does not require a
dataset viewer, live model inference, or user-input collection.

## Required next controls

The publication-candidate assembly must:

1. derive only from the exact reviewed release-pack bytes;
2. retain the reviewed source hashes in a publication manifest;
3. add the reviewed YAML card metadata;
4. add CC BY 4.0 license and attribution files;
5. add a rollback and unpublish runbook;
6. rerun secret, path, privacy, and claim-boundary checks; and
7. remain local until the user explicitly authorizes upload.

## Blocked actions

This ADR does not authorize:

- uploading to Hugging Face;
- changing the reviewed metrics or claims;
- including raw archives, traces, prompts, or model payloads;
- licensing the entire SpecSafe repository under CC BY 4.0; or
- presenting the candidate as promoted or production-ready.

## External references reviewed

- Creative Commons Attribution 4.0 International:
  `https://creativecommons.org/licenses/by/4.0/`
- Hugging Face Hub license identifiers:
  `https://huggingface.co/docs/hub/repositories-licenses`
- Hugging Face Dataset Card metadata:
  `https://huggingface.co/docs/hub/datasets-cards`

## Consequences

### Positive

- Resolves the previously blocked license decision.
- Keeps licensing scope narrow and auditable.
- Prepares valid Hugging Face metadata without modifying the reviewed source pack.
- Preserves the negative-evidence and non-promotion boundaries.
- Keeps actual publication behind one final explicit gate.

### Negative

- The local release pack is still not directly uploadable.
- A separate publication-candidate assembly is required.
- The SpecSafe source repository remains without a repository-wide license decision.
- Final upload still requires owner authorization and platform credentials.

## Next implementation slice

```text
branch=feat/hugging-face-publication-candidate
scope=local Hugging Face Dataset candidate, license, attribution, publication manifest,
      rollback runbook, tests, and no upload
actual_publication=false
```
