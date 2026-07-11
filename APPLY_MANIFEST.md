# Apply Manifest

## Slice

```text
branch=feat/hugging-face-space-story-clarity
commit_message=refactor: clarify hugging face space evidence story
actual_space_publication=false
live_inference=false
user_input_collection=false
evidence_contract_changed=false
```

## Add

```text
apps/specsafe-reliability-lab/src/components/policy-case-matrix.tsx
apps/specsafe-reliability-lab/src/components/policy-case-matrix.test.tsx
```

## Replace

```text
APPLY_MANIFEST.md
apps/specsafe-reliability-lab/src/App.tsx
apps/specsafe-reliability-lab/src/App.test.tsx
apps/specsafe-reliability-lab/tests/smoke.spec.ts
docs/design/hugging-face-space-visual-direction.md
docs/runbooks/hugging-face-space-local-visual-shell.md
```

## Delete

```text
apps/specsafe-reliability-lab/src/components/capacity-chart.tsx
apps/specsafe-reliability-lab/src/components/capacity-chart.test.tsx
```

## Story contract

```text
reading_order=north_star_before_detailed_results
north_star=question_method_answer
policy_summary=count_scoreboard
neutral_cases=explicit_and_visible
case_comparison=exact_responsive_matrix
grouped_bar_chart=removed
```

## Frozen evidence source

```text
canonical_index=release/hugging-face-space/specsafe-reliability-lab/evidence_index.json
canonical_index_sha256=de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e
canonical_index_byte_count=9206
canonical_manifest=release/hugging-face-space/specsafe-reliability-lab/evidence_manifest.json
frontend_parser=strict_zod_fail_closed
```

## Required visible outcomes

```text
adaptive_vs_fixed=2 wins / 3 neutral / 1 loss
adaptive_vs_threshold=3 wins / 2 neutral / 1 loss
neutral_vs_fixed=MPC5-101,MPC5-102,MPC5-106
loss=MPC5-103
wins=MPC5-104,MPC5-105
decision=KEEP_DIAGNOSTIC_ONLY
failure_label=ranking_safety_regression
safety_breach_multiple=24.356617647058766
```

## Validation

```powershell
python .\scripts\build_hugging_face_space_evidence_index.py --check

Push-Location .\apps\specsafe-reliability-lab
npm ci
npm audit --audit-level=low
npm run evidence:check
npm run lint
npm run test
npm run build
npm run test:e2e
Pop-Location

python -m pytest
python -m ruff check .
git diff --check
```

## Manual review gate

```text
north_star_understood_before_results=true
neutral_cases_visually_explicit=true
exact_matrix_clearer_than_grouped_bars=true
desktop_review=required
mobile_review=required
publication_authorized=false
```
