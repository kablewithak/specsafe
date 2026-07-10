# SpecSafe PRD Status Reconciliation — 2026-07-10

## Status

Accepted repository-status reconciliation.

## Purpose

The governing Product Requirements Document remains the controlling product and experiment
contract. Its north star, causal-safety rules, evidence hierarchy, privacy controls, publication
controls, and non-claims are unchanged.

Several phase-status statements in PRD v1.2 describe the repository as it existed before the later
V5 synthetic comparison and Kaggle evidence programme. This document reconciles those factual
status statements against committed evidence at:

```text
main_commit=54227a0
latest_merge=Merge pull request #129
reconciliation_date=2026-07-10
```

This reconciliation does not retroactively alter any experiment, gate, threshold, artifact, or
claim.

## Reconciled evidence state

### Causal and synthetic foundation

The repository retains:

- strict causal runtime contracts;
- deterministic causal-safety rejection;
- fixed-length and static-threshold baselines;
- synthetic capacity profiles;
- a shared synthetic utility scorer;
- a research-only calibrated causal load-aware policy;
- an unsafe retrospective negative control excluded from valid scoring;
- a matched same-input policy-comparison harness;
- a controlled synthetic comparison report and Phase 5 gate.

The controlled synthetic Phase 5 boundary is complete. It supports only controlled-fixture claims.
It does not establish production throughput, latency, cost reduction, serving capacity, or a global
policy winner.

### Synthetic calibration

The retained V5 bounded monotone-beta calibrator passed its predeclared frozen synthetic held-out
calibration gate and was eligible for controlled synthetic policy research.

That synthetic result remains distinct from the later Kaggle-derived candidate-calibrator path.

### Kaggle evidence acquisition

The repository retains governed Kaggle evidence for the Qwen model pair, including:

- preflight qualification;
- multiple trace-collection archives;
- analysis and replay diagnostics;
- calibration-readiness diagnostics;
- a retained fixed-bin Laplace isotonic candidate calibrator;
- fit-pool replay;
- a frozen independent holdout collection;
- deterministic independent holdout analysis;
- no-refit independent holdout replay;
- a formal promotion closeout.

The highest accurate label for this path is:

```text
evidence_maturity=kaggle_environment_evaluated
production_serving_validated=false
```

### Candidate-calibrator decision

The retained Kaggle-derived candidate is:

```text
calibrator_artifact_id=v5-qwen-combined-fixed-bin-isotonic-calibrator-v1
decision_outcome=KEEP_DIAGNOSTIC_ONLY
promotion_attempt_status=closed_not_promoted
candidate_disposition=retained_diagnostic_negative_evidence
calibrator_promotion_status=not_authorized_closed_ranking_safety_regression
```

Independent holdout diagnostics recorded:

```text
holdout_record_count=192
holdout_positive_count=136
holdout_negative_count=56
brier_improvement=0.03811936896716564
fixed_bin_ece_improvement=0.10713044469407718
auroc_delta=-0.024356617647058765
maximum_allowed_auroc_degradation=0.001
```

The favorable probability-quality movement does not override the failed ranking-safety gate.

## Reconciled phase status

| Phase | Reconciled status | Boundary |
|---|---|---|
| 0 — Repository and constitution | Complete | Governing repository and scope controls exist. |
| 1 — Contracts and causal boundary | Complete | Runtime non-anticipation is enforced. |
| 2 — Synthetic traces and baselines | Complete | Deterministic fixtures, baselines, unsafe control, and replay exist. |
| 3 — Calibration and confidence fitness | Complete for the retained V5 synthetic path; Kaggle candidate closed negative | Synthetic V5 passed; the later Kaggle candidate failed ranking safety and is not promoted. |
| 4 — Causal load-aware scheduler | Complete for controlled synthetic research only | No Kaggle-derived or production scheduler promotion exists. |
| 5 — Shared policy comparison and reports | Complete for controlled synthetic evidence | Same-input comparison and reporting are retained. |
| 6 — Kaggle small-model evidence | Complete for the current candidate-evaluation path | Trace, fit, holdout replay, and closeout evidence exist. |
| 7 — Public proof release | Not published | Bounded negative-evidence packaging is authorized; positive promotion proof is not. |
| 8 — Final reconciliation and handover | Pending | Complete after the bounded release decision and repository-wide closeout. |

## Current validity and fallback boundary

The current Kaggle-derived candidate is not fit for automated probability-driven scheduling.

```text
automated_scheduling_confidence_status=unfit_use_conservative_fallback
threshold_promotion_status=not_authorized
scheduler_promotion_status=not_authorized
production_claim_status=not_authorized
```

Conservative fallback is the required behavior whenever a runtime path would otherwise depend on
this candidate as trusted calibrated probability.

## Consumed holdout boundary

The independent holdout is consumed promotion evidence. It may not be used to:

- refit the current candidate;
- tune thresholds;
- tune scheduler logic;
- augment a future fit pool;
- repeatedly select replacement methods against known outcomes.

Any successor candidate requires a fresh predeclared protocol, fresh fit evidence, and fresh
independent promotion evidence.

## Next authorized route

The selected next route is:

```text
1. reconcile repository status and public wording
2. build a deterministic local bounded negative-evidence release pack
3. verify sanitization, provenance, hashes, claims, and non-claims
4. make a separate license and publication-readiness decision
5. optionally publish a Hugging Face Dataset and CPU-only precomputed replay surface
6. perform final project reconciliation and handover
```

A new calibrator redesign is deferred. It is not authorized by this reconciliation and is not an
automatic retry after the closed candidate.

## Claims now permitted

- SpecSafe completed a controlled synthetic same-input policy comparison.
- SpecSafe retained Kaggle-measured trace evidence for a documented Qwen model pair and environment.
- The retained Kaggle candidate was replayed without refit on independent holdout evidence.
- Aggregate Brier score and fixed-bin ECE improved on that holdout.
- Ranking safety regressed beyond the declared tolerance.
- The gate rejected promotion and required conservative fallback.

## Claims still forbidden

- The Kaggle-derived candidate calibrator is promoted.
- Any calibrated threshold is promoted.
- A Kaggle-derived scheduler or adaptive-policy utility improvement is proven.
- Hugging Face artifacts demonstrate positive promotion proof.
- Production speed, latency, throughput, cost savings, serving capacity, or readiness is proven.
