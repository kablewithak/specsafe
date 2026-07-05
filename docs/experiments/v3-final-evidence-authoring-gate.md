# V3 Final-Evidence Authoring Gate

## Purpose

This document authorises a fresh V3 hidden final-evaluation corpus after V3 calibration evidence and the V3 confidence artifact were frozen.

It does not author a hidden case, assess the artifact, or evaluate a scheduler.

## Preconditions: satisfied before authoring

| Requirement | Required state |
|---|---|
| V3 calibration corpus | 36 cases, 144 observations, frozen manifest |
| V3 calibration method | `quantile-isotonic-calibration-v1` fitted and retained |
| Artifact and fit report | deterministic rebuilds only |
| V3 hidden final-evaluation corpus | absent before this gate |
| V3 adversarial corpus | absent before this gate |
| Scheduler/capacity policy | absent before this gate |

## Reserved final-evaluation inventory

The final corpus is fixed at 24 cases and 96 observations.

| Capacity family | Reserved case IDs | Cases | Observations | Required workload allocation |
|---|---:|---:|---:|---|
| Light capacity | `CRV3-201`–`CRV3-206` | 6 | 24 | 2 structured text, 2 code, 2 open-ended chat |
| Moderate capacity | `CRV3-207`–`CRV3-212` | 6 | 24 | 2 structured text, 2 code, 2 open-ended chat |
| Saturated capacity | `CRV3-213`–`CRV3-218` | 6 | 24 | 2 structured text, 2 code, 2 open-ended chat |
| Jagged capacity | `CRV3-219`–`CRV3-224` | 6 | 24 | 2 structured text, 2 code, 2 open-ended chat |
| **Total** | `CRV3-201`–`CRV3-224` | **24** | **96** | **8 structured text, 8 code, 8 open-ended chat** |

## Authoring protocol

1. Create each case as a paired runtime input and post-hoc outcome file.
2. Validate the runtime/outcome separation locally.
3. Add one complete capacity family per reviewed branch.
4. Do not run the fitted artifact against individual final cases or partial final families.
5. When all 24 pairs are authored, create a final-evaluation manifest with hashes, byte counts, aggregate hash, split counts, workload counts, and capacity-family counts.
6. Only after the final manifest is merged may one read-only held-out calibration assessment run.

## Required final-case properties

Every final case must:

- use `split=final_evaluation` and `data_role=held_out_evaluation`;
- contain exactly four candidate positions;
- preserve lawful visible-prefix state at every position;
- separate runtime context from outcome labels;
- declare one workload type and one capacity family;
- use newly authored synthetic values;
- avoid explicit references to V1/V2 fixtures, outcomes, calibration values, or learned artifact buckets.

## What this authoring phase must not do

- refit `quantile-isotonic-calibration-v1`;
- alter `calibration_manifest.json`;
- alter calibration case bytes;
- read or write a V3 policy score;
- add capacity-profile implementation code;
- add scheduler behavior;
- create final results before all 24 cases are frozen;
- create V3 adversarial-regression evidence.

## Exit gate

This phase is complete only when:

- all 24 final-evaluation case pairs exist;
- all 96 final observations are present;
- every capacity family and workload allocation matches this document;
- the final-evaluation manifest rebuilds byte-identically;
- the calibration manifest, artifact, and fit report remain unchanged;
- tests reject early evaluation, split mixing, missing pairs, changed bytes, and prohibited V1/V2 references.
