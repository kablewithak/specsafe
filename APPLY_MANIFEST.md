# Apply Manifest

## Slice

```text
branch=feat/bounded-negative-evidence-publication-readiness
commit=feat: review bounded evidence publication readiness
```

## Add

```text
src/specsafe/publication_readiness/__init__.py
src/specsafe/publication_readiness/models.py
src/specsafe/publication_readiness/review.py
scripts/review_bounded_negative_evidence_publication.py
tests/test_bounded_negative_evidence_publication_readiness.py
evidence/release-governance/specsafe-bounded-negative-evidence-v1/publication_readiness_decision.json
docs/adr/ADR-0044-bounded-negative-evidence-publication-readiness-and-license.md
docs/experiments/bounded-negative-evidence-publication-readiness-review.md
```

## Replace

```text
APPLY_MANIFEST.md
```

## Source boundary

```text
source_commit=60755d1
reviewed_release_manifest_sha256=10b02b3a67c726c321d5f20b4350c75925e6bca1485575181b4eee9b70243f3b
reviewed_release_manifest_byte_count=975
```

## Decision boundary

```text
license_identifier=cc-by-4.0
license_scope=sanitized_release_pack_original_materials_only
decision_outcome=READY_FOR_PUBLICATION_CANDIDATE_ASSEMBLY
publication_candidate_assembly_authorized=true
public_upload_authorized=false
```

## Next branch

```text
feat/hugging-face-publication-candidate
```
