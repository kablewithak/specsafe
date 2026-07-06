# SpecSafe V4 Evidence Reservation Manifest

## Purpose

This root records the fixed V4 evidence plan. The calibration corpus remains hash-frozen and
its regularized-isotonic artifact remains calibration-only evidence. The quarantined
final-evaluation case pairs now exist in a physically separate tree. They are not yet
manifest-frozen, scored, compared, or eligible for runtime-control claims.

## Fixed reservation

| Split | Cases | Positions per case | Observations | Current state |
|---|---:|---:|---:|---|
| Calibration | 48 | 4 | 192 | Authored, hash-frozen, and fitted once |
| Final evaluation | 36 | 4 | 144 | Authored and quarantined; manifest not yet frozen |
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
final_evaluation/inputs/cases/CRV4-201.json through CRV4-236.json
final_evaluation/expected_outcomes/cases/CRV4-201.json through CRV4-236.json
```

Runtime inputs and expected outcomes are separate physical assets in both the calibration and
final-evaluation trees. The calibration manifest remains scoped only to `CRV4-101` through
`CRV4-148`; the final assets must receive their own final-evaluation manifest before any
held-out scoring is permitted.

No adversarial asset, final-evaluation manifest, final-evidence index, held-out result,
scheduler, baseline, replay scorer, or runtime-control surface may appear.

## Current authorization

The next authorised artifact is `v4-final-evaluation-manifest-freeze`. Final scoring remains
prohibited until the complete 72-asset final inventory is hash-verified and frozen.
