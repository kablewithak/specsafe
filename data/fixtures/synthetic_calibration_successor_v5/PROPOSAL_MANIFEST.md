# V5 Schema-Only Proposal Manifest

## Purpose

This root reserves a fresh V5 synthetic calibration corpus before any runtime inputs,
expected outcomes, manifests, fitting artifacts, or final-assessment evidence exists.

## Governing scope

- Fixture set: `synthetic-calibration-successor-v5`
- Method constitution: `v5-bounded-monotone-beta-calibration-eligibility-charter-v1`
- Calibration method: `bounded-monotone-beta-calibration-v5`
- Active boundary: schema-only namespace and scenario-family reservation.

## Reserved evidence roles

| Role | Case range | Cases | Positions per case | Observations |
|---|---:|---:|---:|---:|
| Calibration | `CSV5-101..CSV5-148` | 48 | 4 | 192 |
| Final evaluation | `CSV5-201..CSV5-236` | 36 | 4 | 144 |
| Adversarial regression | `CSV5-301..CSV5-312` | 12 | 4 | 48 |

## Current authorised contents

Only these root metadata files may exist at this stage:

```text
PROPOSAL_MANIFEST.md
authoring_ledger.md
scenario_family_registry.json
```

## Explicit exclusions

- No runtime-input or expected-outcome case asset exists.
- No calibration or final-evaluation manifest exists.
- No calibration artifact, fit diagnostic, or held-out result exists.
- No fitting, threshold selection, parameter mutation, scheduler, capacity profile, utility scorer,
  policy comparison, or runtime control is authorised.
- Final-evaluation and adversarial case reservations remain quarantined.
