# SpecSafe V4 Evidence Reservation Manifest

## Purpose

This root records the fixed V4 evidence plan. All four calibration-only case families are
complete, and `calibration_manifest.json` now freezes their exact runtime/outcome asset
inventory. It is not a calibration artifact, scheduler input surface, policy comparison,
or source of final-evaluation evidence.

## Fixed reservation

| Split | Cases | Positions per case | Observations | Current state |
|---|---:|---:|---:|---|
| Calibration | 48 | 4 | 192 | Authored and hash-frozen |
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
byte counts, case-pair inventory, registry provenance hash, and an aggregate asset digest.
Runtime inputs and expected outcomes remain separate physical assets.

No final-evaluation or adversarial asset may appear. No calibration artifact, fit report,
final-evaluation manifest, final-evidence index, or held-out result may appear.

## Current authorization

The next authorised artifact is `v4-calibration-fit-and-diagnostics`. Any fit must consume
only the hash-verified frozen calibration corpus. Scheduler code, baseline execution,
capacity modelling, replay scoring, final-evaluation authoring, and policy comparison remain
prohibited at this boundary.
