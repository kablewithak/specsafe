# SpecSafe V4 Evidence Reservation Manifest

## Purpose

This root records the fixed V4 evidence plan. The active boundary now authorises all four
calibration-only case families: curve coverage, position spread, workload mix, and capacity
contrast. It is not a calibration manifest, calibration artifact, scheduler input surface,
policy comparison, or source of final-evaluation evidence.

## Fixed reservation

| Split | Cases | Positions per case | Observations | Current state |
|---|---:|---:|---:|---|
| Calibration | 48 | 4 | 192 | All calibration cases authored; manifest not yet frozen |
| Final evaluation | 36 | 4 | 144 | Reserved and quarantined |
| Adversarial regression | 12 | 4 | 48 | Reserved and quarantined |

The full family and case-ID reservation remains in `scenario_family_registry.json`.

## Active physical boundary

At this stage the fixture root may contain:

```text
PROPOSAL_MANIFEST.md
authoring_ledger.md
scenario_family_registry.json
inputs/cases/CRV4-101.json through CRV4-148.json
expected_outcomes/cases/CRV4-101.json through CRV4-148.json
```

Runtime input and expected outcome files are separate physical assets. No final-evaluation or
adversarial asset may appear. No calibration or final manifest, artifact, fit report,
final-evidence index, or held-out result may appear.

## Current authorization

The next authorised artifact is `v4-calibration-manifest-freeze`. Calibration fitting, scheduler
code, baseline execution, capacity modelling, and replay scoring remain prohibited until the
calibration manifest is frozen and its fixture inventory is hash-verified.
