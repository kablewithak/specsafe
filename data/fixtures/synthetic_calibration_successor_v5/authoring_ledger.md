# V5 Authoring Ledger

## Ledger status

```text
fixture_set_id=synthetic-calibration-successor-v5
registry_status=calibration_manifest_frozen
runtime_input_assets=48
expected_outcome_assets=48
calibration_observations_authored=192
calibration_manifest=frozen
calibration_artifact=absent
fit_diagnostics=absent
final_evaluation_assets=0
final_evaluation_manifest=absent
heldout_result=absent
```

## Frozen corpus record

`CSV5-101..CSV5-148` are retained as self-authored synthetic calibration-only case pairs across
curve coverage, position spread, workload variation, and mixed reliability contrast. Runtime
inputs contain only decision-time scheduler context. Candidate token identifiers and post-hoc
labels remain in separate expected-outcome assets.

`calibration_manifest.json` is the immutable inventory boundary for the complete 48-case corpus.
It records the exact source asset hashes, byte counts, aggregate hash, case-pair relationships, and
pre-freeze registry provenance. The active registry anchors the manifest SHA-256 and its
pre-freeze registry SHA-256.

## Evidence boundary

The frozen corpus may not be edited, rebalanced, replaced, or extended. No V5 final-evaluation
asset may be authored, and no V5 policy, capacity, utility, comparison, or runtime-control work is
authorised at this stage.

## Next authorised artifact

`v5-bounded-monotone-beta-fit-diagnostics`
