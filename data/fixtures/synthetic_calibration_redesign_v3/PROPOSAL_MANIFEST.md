# V3 Calibration Authoring Manifest

This directory contains exactly the three authorised V3 calibration families.

## Present at this boundary

- `scenario_family_registry.json`
- `PROPOSAL_MANIFEST.md`
- `authoring_ledger.md`
- runtime-input case pairs `CRV3-101` through `CRV3-136` under `inputs/cases/`
- separate post-hoc outcome case pairs `CRV3-101` through `CRV3-136` under `expected_outcomes/cases/`

## Absent at this boundary

- all `CRV3-201` through `CRV3-224` final-evaluation case pairs
- all `CRV3-301` through `CRV3-308` adversarial-regression case pairs
- every V3 manifest
- every V3 fitted calibration artifact or report
- every V3 scheduler, capacity-profile, policy-comparison, or promotion artifact

The files are local, self-authored synthetic controlled evidence. Runtime input files do not contain candidate token IDs, observed acceptance labels, prefix-survival labels, or final-evaluation data.
