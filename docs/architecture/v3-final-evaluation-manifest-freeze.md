# V3 Final-Evaluation Manifest Freeze

## Purpose

This document defines the manifest-freeze boundary for the complete V3 held-out corpus.

The manifest is an integrity and provenance artifact. It is not an assessment report, scheduler input, policy result, or promotion decision.

## Frozen inventory

```text
Cases: 24
Observations: 96
Candidate positions per case: 4
Assets: 48
```

| Capacity family | Case IDs | Cases | Observations |
|---|---:|---:|---:|
| Light | CRV3-201 to CRV3-206 | 6 | 24 |
| Moderate | CRV3-207 to CRV3-212 | 6 | 24 |
| Saturated | CRV3-213 to CRV3-218 | 6 | 24 |
| Jagged | CRV3-219 to CRV3-224 | 6 | 24 |

Each case retains a physically separate runtime input and expected-outcome file.

## Integrity contract

`final_evaluation_manifest.json` records, for each final-evaluation asset:

- artifact kind;
- contained relative path;
- case ID and scenario family;
- split and data role;
- SHA-256;
- byte count.

It also records the exact hash and byte count of `final_evidence_index.json`. That index already verifies the frozen calibration registry, calibration manifest, quantile-isotonic artifact, and fit report.

Any change to a held-out case, outcome label, final-evidence index, or manifest aggregate makes the frozen final corpus fail to load.

## Explicit boundary

The manifest-freeze code may:

- discover and validate the complete authored held-out inventory;
- verify schema, runtime/outcome alignment, family membership, capacity profile membership, hashes, and byte counts;
- write or re-read deterministic manifest bytes.

It may not:

- fit or invoke the calibrator against held-out evidence;
- compute a held-out metric;
- make a scheduler, policy, eligibility, or promotion decision;
- alter a held-out case pair;
- alter frozen calibration evidence;
- add adversarial-regression evidence.

## Next authorised action

The next authorised artifact is the one-time V3 final assessment. Before that action, the repository is at the formal handover boundary.
