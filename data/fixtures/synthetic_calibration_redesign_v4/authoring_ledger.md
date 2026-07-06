# V4 Evidence Authoring Ledger

## Current stage

`final_heldout_calibration_assessed`

## Authoring record

| Artifact class | Status | Evidence role |
|---|---|---|
| V4 scenario-family registry | Updated | Retained frozen provenance, result hash, status, and remediation route |
| Calibration runtime/outcome pairs, CRV4-101 through CRV4-148 | Frozen | Calibration-only evidence |
| Calibration manifest | Frozen | Immutable 96-asset calibration inventory |
| Regularized-isotonic calibration artifact | Frozen | Calibration-only monotonic confidence map |
| Regularized-isotonic fit report | Frozen | Fit-data diagnostics only |
| Final runtime/outcome pairs, CRV4-201 through CRV4-236 | Frozen and consumed | One held-out calibration gate |
| Final-evaluation manifest | Frozen | Immutable 72-asset held-out inventory |
| Final-evidence index | Frozen | Deterministic case, trace, workload, and capacity provenance |
| Held-out assessment result | Frozen | Write-once V4 final calibration evidence |
| ADR-0016 remediation decision | Accepted | V4 closeout and fresh-programme route |
| Adversarial runtime inputs and outcomes | Not authored | Remain quarantined; not a remediation substitute |
| Scheduler, baselines, replay scorer, and runtime control | Not authored | Blocked by the held-out ranking-safety regression |

## Retained outcome

```text
status: RANKING_SAFETY_REGRESSION
brier_score_improvement: +0.035430737397
ece_10_bin_improvement: +0.038425154321
auroc_delta: -0.012890625000
policy research eligibility: blocked
fallback policy: fixed_short_1
```

The held-out assessment was complete and valid. Probability calibration quality improved, but the
ranking-safety gate failed. V4 is therefore retained as valid negative evidence rather than patched
or rerun.

## Integrity statement

The 48 calibration case pairs remain protected by their immutable 96-asset manifest. The 36 final
case pairs remain in a separate held-out tree protected by a 72-asset final manifest and a label-free
final-evidence index. The assessment result is canonical, hash-anchored, and write-once.

Runtime assets never contain candidate token IDs, observed acceptance labels, or prefix-survival
labels. No V4 policy, baseline, replay, scheduler, runtime-control, deployment, or production claim
exists.

## Next closeout boundary

`v4-closeout-q-and-a-and-handover`

No new V4 technical artifact is authorized before the formal handover. A later successor programme
must start with a fresh method-and-evidence constitution.
