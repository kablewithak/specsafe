# V3 Quantile-Isotonic Calibration Fit

## Purpose

This boundary fits the predeclared `quantile-isotonic-calibration-v1` method against the
frozen V3 calibration manifest only.

It turns 144 fresh calibration observations into a deterministic, monotonic confidence map.
It does not decide whether that map is good enough for automated policy decisions. That
answer is reserved for one later held-out assessment on separately authored, locked V3
final-evaluation evidence.

## Inputs

The fitter accepts only a verified
`CalibrationRedesignV3CalibrationManifestedFixtureSet` loaded from:

```text
data/fixtures/synthetic_calibration_redesign_v3/calibration_manifest.json
```

The manifest locks exactly:

```text
36 calibration cases
144 observations
72 separate runtime/outcome files
3 calibration families
```

The fitter rejects foreign objects, non-calibration evidence, non-finite confidence values,
invalid confidence ranges, insufficient groups, and all-one-label corpora.

## Fixed method

The method was chosen before V3 data existed and is not tuned here.

1. Sort the 144 observations by raw confidence, then stable case and position keys.
2. Split them into eight equal-count groups of 18 observations.
3. Calculate each group's Laplace-smoothed observed acceptance rate:

```text
(successes + 1) / (observations + 2)
```

4. Apply weighted pooled-adjacent-violators merging whenever a higher-confidence group has
a lower learned rate than the group before it.
5. Bound output confidence to the predeclared range `0.02` to `0.98`.
6. Retain the resulting eight-bin, non-decreasing map as JSON evidence.

## Retained outputs

```text
evidence/calibration/quantile-isotonic-calibration-v1/artifact.json
evidence/calibration/quantile-isotonic-calibration-v1/fit_report.json
```

The retained output records provenance, the frozen calibration-manifest hash, sample counts,
quantile boundaries, smoothing, pooled blocks, and calibration-split metrics.

It does not contain policy actions, capacity decisions, scheduler configuration, utility
scores, a held-out gate result, or a promotion decision.

## Calibration-split result

On the frozen calibration corpus, the deterministic map improves the in-sample diagnostic
metrics:

```text
raw Brier score:        0.1807659722
calibrated Brier score: 0.1569227431

raw 10-bin ECE:         0.1400694444
calibrated 10-bin ECE:  0.0366319444
```

These are calibration-split diagnostics only. They are not proof of held-out calibration
quality, policy value, throughput, production cost savings, or eligibility for automated
scheduling.

## Boundary

This fit may not:

- read V3 final-evaluation or adversarial assets;
- modify any V3 calibration input, outcome, registry, or manifest byte;
- choose a different method, bin count, smoothing rule, threshold, or policy rule;
- create capacity profiles, scheduler actions, policy comparisons, or promotion claims.

## Next authorised work

The next boundary is a calibration-readiness and final-evidence authoring gate. It must keep
the fitted artifact fixed and must define how fresh V3 hidden final-evaluation evidence will
be authored, locked, assessed once, and compared fairly.
