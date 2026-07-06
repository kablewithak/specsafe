# V3 Authoring Ledger

## Current boundary

- **Boundary:** V3 quantile-isotonic calibration fit.
- **V3 calibration runtime inputs authored:** 36 of 36 cases.
- **V3 calibration expected outcomes authored:** 36 of 36 cases.
- **V3 calibration observations authored:** 144 of 144.
- **V3 final-evaluation runtime inputs authored:** no.
- **V3 final-evaluation expected outcomes authored:** no.
- **V3 adversarial-regression runtime inputs authored:** no.
- **V3 adversarial-regression expected outcomes authored:** no.
- **V3 manifests authored:** calibration manifest only.
- **V3 calibration fit authored:** `quantile-isotonic-calibration-v1` only.
- **V3 policy or scheduler code authored:** no.
- **V1/V2 data-bearing evidence used:** no.

## Authored families

| Family | Case IDs | Cases | Observations | Purpose |
|---|---|---:|---:|---|
| `CRV3-CAL-CURVE-COVERAGE` | `CRV3-101` to `CRV3-112` | 12 | 48 | Fresh raw-confidence coverage for the fixed eight-group calibration method. |
| `CRV3-CAL-POSITION-SPREAD` | `CRV3-113` to `CRV3-124` | 12 | 48 | Fresh position-spread coverage across the fixed four-position V3 contract. |
| `CRV3-CAL-WORKLOAD-MIX` | `CRV3-125` to `CRV3-136` | 12 | 48 | Fresh workload-mix coverage across structured text, code, and open-ended chat. |

The complete calibration corpus now contains broad confidence coverage, deliberate position variation, and a controlled workload-dependent confidence shift. Runtime inputs retain only lawful pre-sample confidence and visible-prefix state. This is synthetic controlled evidence only, not a production claim.

## Still reserved and absent

| Split / family | Cases | Observations | Status |
|---|---:|---:|---|
| Final evaluation | 24 | 96 | Quarantined reservation only |
| Adversarial regression | 8 | 32 | Reserved, absent |

## Next authorisation

`v3-calibration-manifest-authoring`

The next authorised slice may freeze the completed V3 calibration corpus behind a deterministic calibration manifest. Final-evaluation and adversarial bytes remain absent and quarantined.


## V3 calibration manifest freeze

- `calibration_manifest.json` freezes the complete 36-case / 144-observation V3 calibration corpus.
- Every runtime and expected-outcome case asset is hash-addressed with byte counts.
- V3 final-evaluation and adversarial-regression bytes remain absent.
- No calibration fitting, scheduler behaviour, policy comparison, or promotion decision is authorised by this freeze.

## V3 quantile-isotonic calibration fit

- The predeclared `quantile-isotonic-calibration-v1` method was fitted only against the frozen V3 calibration manifest.
- Retained evidence: `evidence/calibration/quantile-isotonic-calibration-v1/artifact.json` and `fit_report.json`.
- Calibration-split diagnostics were retained for traceability only; no V3 final-evaluation asset was read.
- No held-out calibration gate, adaptive-policy eligibility, scheduler behaviour, capacity profile, policy comparison, or promotion decision is authorised by this fit.
- V3 final-evaluation and adversarial evidence remains absent and quarantined.

## Next authorisation

`v3-calibration-readiness-and-final-evidence-authoring-gate`

The next slice may define the pre-authoring gate for fresh V3 hidden final-evaluation evidence. It must keep the frozen calibration corpus and fitted artifact unchanged.


## Final evidence index and light-capacity family

- Added `final_evidence_index.json` as a separate held-out inventory so final authoring does not alter the frozen calibration registry.
- Recorded hashes for the frozen calibration registry, calibration manifest, quantile-isotonic artifact, and fit report.
- Authored `CRV3-201` through `CRV3-206` as separate held-out light-capacity runtime and outcome pairs under `final_evaluation/`.
- Did not create a V3 final-evaluation manifest, run a held-out assessment, run the fitted calibrator on held-out data, add scheduler logic, or create adversarial evidence.


## Final evidence index and moderate-capacity family

- Updated `final_evidence_index.json` without touching the frozen calibration registry, calibration manifest, quantile-isotonic artifact, or fit report.
- Authored `CRV3-207` through `CRV3-212` as separate held-out moderate-capacity runtime and outcome pairs under `final_evaluation/`.
- The held-out inventory now contains 12 of 24 case pairs and 48 of 96 observations.
- Workload balance remains two `structured_text`, two `code`, and two `open_ended_chat` cases for the moderate-capacity family.
- Did not create a V3 final-evaluation manifest, run a held-out assessment, run the fitted calibrator against held-out evidence, add scheduler logic, or author adversarial evidence.

## Final evidence index and saturated-capacity family

- Updated `final_evidence_index.json` without touching the frozen calibration registry, calibration manifest, quantile-isotonic artifact, or fit report.
- Authored `CRV3-213` through `CRV3-218` as separate held-out saturated-capacity runtime and outcome pairs under `final_evaluation/`.
- The held-out inventory now contains 18 of 24 case pairs and 72 of 96 observations.
- Workload balance remains two `structured_text`, two `code`, and two `open_ended_chat` cases for the saturated-capacity family.
- Did not create a V3 final-evaluation manifest, run a held-out assessment, run the fitted calibrator against held-out evidence, add scheduler logic, or author adversarial evidence.

## Next authorisation

`v3-final-jagged-capacity-fixtures`

The next authorised slice may add only `CRV3-219` through `CRV3-224` under the separate final-evaluation subtree. Frozen calibration assets remain unchanged.
