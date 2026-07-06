# SpecSafe V4 Evidence Reservation Manifest

## Purpose

This root records the fixed V4 evidence plan. The calibration corpus remains hash-frozen and its
regularized-isotonic artifact remains calibration-only evidence. The 36 quarantined final cases
now have an immutable final-evaluation manifest and final-evidence index. Those files preserve
provenance; they are not a held-out assessment, policy comparison, or runtime-control result.

## Fixed reservation

| Split | Cases | Positions per case | Observations | Current state |
|---|---:|---:|---:|---|
| Calibration | 48 | 4 | 192 | Authored, hash-frozen, and fitted once |
| Final evaluation | 36 | 4 | 144 | Authored and hash-frozen; assessment not run |
| Adversarial regression | 12 | 4 | 48 | Reserved and quarantined |

The complete family and case-ID reservation remains in `scenario_family_registry.json`.

## Active physical boundary

At this stage the fixture root may contain:

```text
PROPOSAL_MANIFEST.md
authoring_ledger.md
scenario_family_registry.json
calibration_manifest.json
final_evaluation_manifest.json
final_evidence_index.json
inputs/cases/CRV4-101.json through CRV4-148.json
expected_outcomes/cases/CRV4-101.json through CRV4-148.json
final_evaluation/inputs/cases/CRV4-201.json through CRV4-236.json
final_evaluation/expected_outcomes/cases/CRV4-201.json through CRV4-236.json
```

Runtime inputs and expected outcomes remain physically separate in both evidence trees. The
calibration manifest covers only `CRV4-101` through `CRV4-148`. The final-evaluation manifest and
index cover only `CRV4-201` through `CRV4-236`.

No adversarial asset, held-out assessment, scheduler, baseline, replay scorer, policy comparison,
or runtime-control surface may appear.

## Current authorization

The next authorized artifact is `v4-final-heldout-calibration-assessment`. That assessment must
consume only the frozen calibration artifact, the frozen final manifest, and the frozen final
evidence index. It is write-once. No policy work is authorized at this boundary.
