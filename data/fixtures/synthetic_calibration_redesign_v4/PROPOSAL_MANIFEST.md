# SpecSafe V4 Evidence Reservation Manifest

## Purpose

This root records the fixed V4 evidence programme and its completed held-out calibration result.
The calibration corpus, the final-evaluation corpus, the regularized-isotonic artifact, the fit
report, the final manifest, the label-free final-evidence index, and the held-out result are
immutable historical evidence.

ADR-0016 closes V4 after a valid `RANKING_SAFETY_REGRESSION`. V4 is not eligible for policy,
baseline, replay, scheduler, runtime-control, deployment, or production-readiness work.

## Fixed reservation and final state

| Split | Cases | Positions per case | Observations | Final state |
|---|---:|---:|---:|---|
| Calibration | 48 | 4 | 192 | Authored, hash-frozen, and fitted once |
| Final evaluation | 36 | 4 | 144 | Authored, hash-frozen, assessed once, and consumed |
| Adversarial regression | 12 | 4 | 48 | Reserved and quarantined; not authorized as remediation |

The complete family and case-ID reservation remains in `scenario_family_registry.json`.

## Held-out result

The retained assessment is:

```text
evidence/heldout-calibration/v4-final-heldout-calibration-assessment-v1/result.json
```

```text
status: RANKING_SAFETY_REGRESSION
brier_score_improvement: +0.035430737397
ece_10_bin_improvement: +0.038425154321
auroc_delta: -0.012890625000
adaptive_policy_research_eligibility: blocked
fallback_policy_id: fixed_short_1
```

The result passed provenance, coverage, no-refit, no-policy-execution, Brier, and ECE checks. It
failed the predeclared AUROC ranking-safety condition. The retained result is accepted negative
evidence, not an implementation defect.

## Active physical boundary

At V4 closeout, this fixture root may contain:

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

The write-once assessment result remains outside the fixture root under
`evidence/heldout-calibration/`.

Runtime inputs and expected outcomes remain physically separate in both evidence trees. The
calibration manifest covers only `CRV4-101` through `CRV4-148`. The final-evaluation manifest and
index cover only `CRV4-201` through `CRV4-236`.

## Closure boundary

No V4 calibration refit, new V4 final fixture, assessment rerun, threshold change, scheduler,
baseline, replay scorer, policy comparison, capacity policy, runtime-control surface, or
production claim is authorized.

The next immediate artifact is the formal V4 closeout handover after the architecture Q&A review.
A fresh successor programme, if pursued, requires a new method-and-evidence constitution and fresh
evidence; it may not tune against V4 held-out outcomes.
