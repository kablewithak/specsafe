# Hugging Face Space Evidence Index Result

## Result

A frozen, read-only evidence index is retained at:

```text
release/hugging-face-space/specsafe-reliability-lab/evidence_index.json
```

Its companion manifest is retained at:

```text
release/hugging-face-space/specsafe-reliability-lab/evidence_manifest.json
```

## Visitor-facing summary

> Adaptive verification helped under some conditions, was neutral under others, and lost in one.
> When the real confidence signal failed its safety gate, SpecSafe blocked activation.

## Included evidence

```text
valid_causal_comparisons=6
unsafe_retrospective_controls_excluded=6
adaptive_vs_fixed=2 higher, 3 neutral, 1 lower
adaptive_vs_threshold=3 higher, 2 neutral, 1 lower
holdout_record_count=192
decision_outcome=KEEP_DIAGNOSTIC_ONLY
failure_label=ranking_safety_regression
public_dataset_verified=true
```

## Output identity

```text
evidence_index_byte_count=9206
evidence_index_sha256=de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e
```

## Product boundary

The evidence index is not the Space UI. It is the frozen content and provenance contract that the
visual layer will consume.

It contains no live inference, secrets, user input, raw prompts, raw traces, client data, or mutable
controls.

## Reproduction

```powershell
python .\scripts\build_hugging_face_space_evidence_index.py --check
```

## Next gate

Build the visually polished read-only Space shell using React, TypeScript, Tailwind CSS, shadcn/ui,
and Recharts. Keep the quick summary first, make the difference between scheduler value and failed
confidence activation obvious, and retain technical details behind optional evidence views.
