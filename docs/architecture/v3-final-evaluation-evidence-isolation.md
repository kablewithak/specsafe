# V3 Final-Evaluation Evidence Isolation

## Boundary

V3 has three evidence zones. Information may move only in the allowed direction.

```text
V3 calibration corpus
  -> frozen V3 calibration manifest
  -> frozen quantile-isotonic artifact

Fresh V3 final-evaluation corpus
  -> frozen V3 final-evaluation manifest
  -> one read-only held-out calibration assessment

V3 adversarial regression corpus
  -> later regression protection only
```

The final-evaluation corpus is not an input to fitting. It exists only to test the already frozen V3 artifact.

## Prohibited paths

```text
V3 final evidence -> V3 calibrator fitting                 prohibited
V3 final outcomes -> calibration case authoring            prohibited
V3 final results -> changed artifact or thresholds         prohibited
V2 evidence -> V3 final-case design                        prohibited
V3 policy score -> V3 final-case authoring                 prohibited
```

## Required artifact guards

During final-evidence authoring and assessment, the following artifacts must remain byte-identical:

- `data/fixtures/synthetic_calibration_redesign_v3/calibration_manifest.json`
- `evidence/calibration/quantile-isotonic-calibration-v1/artifact.json`
- `evidence/calibration/quantile-isotonic-calibration-v1/fit_report.json`

The final-evaluation manifest is added only after all final case pairs are authored.

## Final-evaluation report eligibility

A V3 held-out calibration report may be written only if:

1. the final manifest validates every case-pair hash;
2. the manifest covers exactly 24 cases and 96 observations;
3. the fitted artifact references the frozen calibration manifest only;
4. no final case was used during fitting;
5. the assessment is deterministic and retained;
6. the report explicitly records whether calibration passed its predeclared gate.

A passing held-out calibration assessment permits later causal-policy work. A failing assessment blocks probability-driven scheduler admission and requires the declared conservative fallback path.

## Why this matters

A final score is useful only if it answers a question the project had not already tuned itself to answer. This isolation boundary protects that value.
