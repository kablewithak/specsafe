# SpecSafe V4 Evidence Reservation Manifest

## Purpose

This root records the fixed V4 evidence plan. All four calibration-only case families and
`calibration_manifest.json` remain frozen. The regularized-isotonic calibration artifact and
fit report are retained outside this fixture root under
`evidence/calibration/regularized-isotonic-calibration-v4/` and are tied back to this root by
manifest and registry hashes. They are calibration-only diagnostics, not policy or held-out
performance evidence.

## Fixed reservation

| Split | Cases | Positions per case | Observations | Current state |
|---|---:|---:|---:|---|
| Calibration | 48 | 4 | 192 | Authored, hash-frozen, and fitted once |
| Final evaluation | 36 | 4 | 144 | Reserved and quarantined |
| Adversarial regression | 12 | 4 | 48 | Reserved and quarantined |

The complete family and case-ID reservation remains in `scenario_family_registry.json`.

## Active physical boundary

At this stage the fixture root may contain:

```text
PROPOSAL_MANIFEST.md
authoring_ledger.md
scenario_family_registry.json
calibration_manifest.json
inputs/cases/CRV4-101.json through CRV4-148.json
expected_outcomes/cases/CRV4-101.json through CRV4-148.json
```

`calibration_manifest.json` records the exact 96 calibration asset paths, SHA-256 hashes,
byte counts, case-pair inventory, frozen registry provenance hash, and an aggregate asset
digest. Runtime inputs and expected outcomes remain separate physical assets.

No final-evaluation or adversarial asset may appear. No final-evaluation manifest,
final-evidence index, or held-out result may appear in this fixture root.

## Current authorization

The next authorised artifact is `v4-final-evaluation-fixture-authoring`. Final-evaluation
assets remain quarantined until their own authoring boundary is introduced. Scheduler code,
baseline execution, capacity modelling, replay scoring, policy comparison, and runtime control
remain prohibited.
