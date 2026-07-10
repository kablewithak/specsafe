# SpecSafe Bounded Negative-Evidence Hugging Face Publication Candidate

## Result

A deterministic local Hugging Face Dataset publication candidate was assembled from the exact reviewed bounded negative-evidence release pack and publication-readiness decision.

```text
candidate_id=specsafe-bounded-negative-evidence-hf-candidate-v1
repository_type=dataset
repository_name=specsafe-bounded-negative-evidence-v1
validity_marker=CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY
license_identifier=cc-by-4.0
publication_status=local_candidate_upload_not_authorized
public_upload_authorized=false
```

No Hugging Face repository was created or modified.

## Source boundary

```text
source_commit=38b2993
publication_readiness_decision_sha256=51cf44163f1656a62035475ad217271046bc0cf6c8f21d12bff22f65a5341790
source_release_manifest_sha256=10b02b3a67c726c321d5f20b4350c75925e6bca1485575181b4eee9b70243f3b
```

The builder verifies the readiness decision, the reviewed release manifest, and every reviewed source file before assembling the candidate.

## Candidate contents

```text
release/hugging-face/specsafe-bounded-negative-evidence-v1/
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

The candidate includes no row-level dataset, raw prompt or trace payload, archive, model payload, live inference, environment dump, credential, or user-input collection.

## Derivation

- `README.md` is the exact reviewed dataset-card body with the approved Hugging Face YAML metadata prepended.
- `evidence_boundary.md` is an exact reviewed source copy.
- `release_summary.json` is an exact reviewed source copy.
- `source_release_manifest.json` is an exact reviewed source copy.
- License, attribution, rollback, sanitization, and publication-manifest files are deterministically generated governance materials.

## Final sanitization result

```text
scanned_file_count=9
forbidden_marker_matches=0
final_result=PASS_LOCAL_CANDIDATE_ONLY
public_upload_authorized=false
```

The final scan covers every candidate file, including `publication_manifest.json`.

## Candidate manifest

```text
publication_manifest_sha256=6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6
publication_manifest_byte_count=4135
```

The manifest retains the exact reviewed source hashes and the SHA-256 and byte count for every pre-manifest candidate file.

## License boundary

CC BY 4.0 applies only to the original sanitized publication-candidate materials. It does not license the complete SpecSafe source repository, retained Kaggle archives, raw traces or prompts, the candidate calibrator artifact, or upstream models and their outputs.

This is an engineering distribution choice, not legal advice.

## Reproduction

```powershell
python .\scripts\build_hugging_face_publication_candidate.py --check
```

The canonical check validates source integrity, strict schemas, metadata, license scope, attribution, rollback controls, final sanitization, claim boundaries, exact file allowlists, and byte-identical committed candidate output.

## Next gate

Create an explicit publication-authorization decision tied to the exact candidate manifest SHA-256.

That decision may authorize or reject a later upload. This candidate-assembly slice performs no upload and contains no credentials or platform mutation code.
