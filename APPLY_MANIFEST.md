# Apply Manifest

## Slice

```text
branch=feat/hugging-face-publication-candidate
commit_message=feat: assemble hugging face publication candidate
actual_publication=false
```

## Add

```text
src/specsafe/hugging_face_publication_candidate/__init__.py
src/specsafe/hugging_face_publication_candidate/models.py
src/specsafe/hugging_face_publication_candidate/builder.py
scripts/build_hugging_face_publication_candidate.py
tests/test_hugging_face_publication_candidate.py
release/hugging-face/specsafe-bounded-negative-evidence-v1/ATTRIBUTION.md
release/hugging-face/specsafe-bounded-negative-evidence-v1/LICENSE.md
release/hugging-face/specsafe-bounded-negative-evidence-v1/README.md
release/hugging-face/specsafe-bounded-negative-evidence-v1/ROLLBACK.md
release/hugging-face/specsafe-bounded-negative-evidence-v1/evidence_boundary.md
release/hugging-face/specsafe-bounded-negative-evidence-v1/publication_manifest.json
release/hugging-face/specsafe-bounded-negative-evidence-v1/release_summary.json
release/hugging-face/specsafe-bounded-negative-evidence-v1/sanitization_report.json
release/hugging-face/specsafe-bounded-negative-evidence-v1/source_release_manifest.json
docs/experiments/bounded-negative-evidence-hugging-face-publication-candidate.md
```

## Replace

```text
APPLY_MANIFEST.md
```

## Governing source artifacts

```text
publication_readiness_decision_sha256=51cf44163f1656a62035475ad217271046bc0cf6c8f21d12bff22f65a5341790
source_release_manifest_sha256=10b02b3a67c726c321d5f20b4350c75925e6bca1485575181b4eee9b70243f3b
```

## Result

```text
candidate_id=specsafe-bounded-negative-evidence-hf-candidate-v1
publication_manifest_sha256=6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6
validity_marker=CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY
publication_status=local_candidate_upload_not_authorized
public_upload_authorized=false
```

## Validation

```powershell
python .\scripts\build_hugging_face_publication_candidate.py --check
python -m json.tool .\release\hugging-face\specsafe-bounded-negative-evidence-v1\publication_manifest.json | Out-Null
python -m json.tool .\release\hugging-face\specsafe-bounded-negative-evidence-v1\sanitization_report.json | Out-Null
python -m pytest .\tests\test_hugging_face_publication_candidate.py
python -m pytest .\tests\test_bounded_negative_evidence_publication_readiness.py
python -m pytest .\tests\test_bounded_negative_evidence_release.py
python -m pytest
python -m ruff check .
python -m ruff format --check .\src\specsafe\hugging_face_publication_candidate .\scripts\build_hugging_face_publication_candidate.py .\tests\test_hugging_face_publication_candidate.py
git diff --check
```
