# Apply Manifest

## Slice

```text
branch=feat/hugging-face-publication-authorization
commit_message=feat: authorize exact hugging face publication
actual_publication=false
```

## Add

```text
src/specsafe/publication_authorization/__init__.py
src/specsafe/publication_authorization/models.py
src/specsafe/publication_authorization/review.py
scripts/authorize_hugging_face_dataset_publication.py
tests/test_hugging_face_publication_authorization.py
evidence/release-governance/specsafe-bounded-negative-evidence-v1/publication_authorization_decision.json
docs/adr/ADR-0045-authorize-exact-hugging-face-dataset-publication.md
docs/experiments/bounded-negative-evidence-publication-authorization.md
docs/product/hugging-face-space-visual-direction.md
```

## Replace

```text
APPLY_MANIFEST.md
```

## Governing candidate

```text
source_commit=489ebb5
publication_manifest_sha256=6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6
publication_manifest_byte_count=4135
publication_authorization_decision_sha256=bf96e015379f8ad955791c28b8ba75b123b3d748d2192943190b056eb5aadc46
```

## Result

```text
decision_outcome=AUTHORIZE_EXACT_PUBLICATION
publication_authorized=true
publication_performed=false
repository_type=dataset
repository_name=specsafe-bounded-negative-evidence-v1
visibility=public
gated=false
```

## Validation

```powershell
python .\scripts\authorize_hugging_face_dataset_publication.py --check
python -m json.tool .\evidence\release-governance\specsafe-bounded-negative-evidence-v1\publication_authorization_decision.json | Out-Null
python -m pytest .\tests\test_hugging_face_publication_authorization.py
python -m pytest .\tests\test_hugging_face_publication_candidate.py
python -m pytest
python -m ruff check .
python -m ruff format --check .\src\specsafe\publication_authorization .\scripts\authorize_hugging_face_dataset_publication.py .\tests\test_hugging_face_publication_authorization.py
git diff --check
```
