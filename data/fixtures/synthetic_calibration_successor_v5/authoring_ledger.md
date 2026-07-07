# V5 Authoring Ledger

## Ledger status

```text
fixture_set_id=synthetic-calibration-successor-v5
registry_status=calibration_fit_diagnostics_retained
runtime_input_assets=48
expected_outcome_assets=48
calibration_observations_authored=192
calibration_manifest=frozen
calibration_artifact=retained
fit_diagnostics=retained
final_evaluation_assets=0
final_evaluation_manifest=absent
heldout_result=absent
```

## Frozen corpus and fit record

`CSV5-101..CSV5-148` remain self-authored synthetic calibration-only case pairs across curve
coverage, position spread, workload variation, and mixed reliability contrast. Runtime inputs
contain decision-time scheduler context only. Candidate token identifiers and post-hoc labels
remain in separate expected-outcome assets.

`calibration_manifest.json` is the immutable 48-case inventory boundary. It records exact source
asset hashes, byte counts, aggregate hash, case-pair relationships, and pre-freeze registry
provenance.

`bounded_monotone_beta_calibration_artifact.json` retains the single predeclared V5 global
bounded monotone-beta transform fitted from the frozen calibration corpus only.
`bounded_monotone_beta_calibration_fit_diagnostics.json` retains the deterministic optimizer
record, calibration-only probability diagnostics, monotonicity verification, and exact artifact
hash. Diagnostics use an explicit 12-decimal round-half-even persistence precision so harmless
sub-ULP floating-point variation cannot change canonical evidence bytes across supported Python
runtimes. The calibration artifact parameters are not rounded or changed by this control.

## Evidence boundary

The calibration corpus, artifact, and diagnostics are audit-only calibration evidence. They may
not be edited, rebalanced, replaced, refit, or used as a hidden policy-selection result. No V5
final-evaluation asset may be authored outside the next explicitly authorised final-fixture stage.
No scheduler, capacity, utility, comparison, or runtime-control work is authorised at this stage.

## Next authorised artifact

`v5-final-evaluation-fixture-authoring`
