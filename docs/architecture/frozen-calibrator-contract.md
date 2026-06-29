# Frozen Calibrator Contract

## Purpose

This boundary fits a deterministic equal-width histogram calibration artifact from immutable
`calibration`-split fixtures only. It is the bridge between raw-confidence diagnostics and a
later held-out calibration-fitness assessment. It is not a runtime scheduling feature.

## Fit boundary

```text
SyntheticTraceFixtureSet
  -> select calibration split only
  -> join confidence with post-hoc acceptance outcomes
  -> fit and freeze histogram bins
  -> persist typed JSON artifact if requested
```

The fitter accepts only the exact `SyntheticTraceFixtureSet` contract. It filters cases by
`TraceSplit.CALIBRATION`. Development, adversarial-regression, and final-evaluation cases are
not read, selected, scored, retained, or used to define any bin value.

## Artifact contents

Every `FrozenCalibratorArtifact` retains:

- fit protocol ID, bin count, and minimum source observation requirement;
- fixture-set ID and version;
- calibration-only case and trace IDs;
- source observation count and global observed acceptance rate;
- every equal-width bin's boundaries, source-observation count, measured acceptance rate when
  populated, and deterministic applied probability;
- an immutable status of `frozen_pending_held_out_fitness`;
- an immutable runtime-control status of `not_eligible_pending_held_out_fitness`.

For an empty bin, the artifact records no observed acceptance rate. Its applied probability is
the retained calibration-set global acceptance rate. This makes fallback behavior explicit
without inventing bin-specific evidence.

## Application boundary

`apply_frozen_calibrator(...)` maps a scalar raw confidence to the frozen bin value. It does
not consume a trace, outcome label, candidate token, capacity state, scheduler context, or
policy action. It does not authorize an admission, stop, threshold, or adaptive control path.

## Held-out separation

The final-evaluation split is reserved for the next boundary. Tests mutate final-evaluation
outcomes in a copy of the fixture set and prove the fitted artifact is unchanged. This is a
structural anti-leakage regression, not a held-out performance result.

## Current non-claims

This boundary does not establish that calibration improved Brier score or ECE on held-out data.
It does not authorize a calibrated threshold, load-aware scheduler, utility score, policy
winner, throughput improvement, losslessness claim, or production behavior.
