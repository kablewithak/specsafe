# ADR-0042: Close Candidate-Calibrator Promotion as Diagnostic-Only Negative Evidence

## Status

Accepted

## Date

2026-07-10

## Context

ADR-0041 required an independent holdout replay before the retained candidate calibrator could be promoted beyond diagnostic status.

That replay is now complete for:

```text
candidate_calibrator=v5-qwen-combined-fixed-bin-isotonic-calibrator-v1
holdout_archive=v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4
holdout_records=192
holdout_positives=136
holdout_negatives=56
no_refit_passed=true
```

The independent replay produced mixed evidence:

```text
raw_brier_score=0.18747805218884495
calibrated_brier_score=0.1493586832216793
brier_improvement=0.03811936896716564

raw_fixed_bin_ece=0.20698108013796931
calibrated_fixed_bin_ece=0.09985063544389214
fixed_bin_ece_improvement=0.10713044469407718

raw_auroc=0.881827731092437
calibrated_auroc=0.8574711134453782
auroc_delta=-0.024356617647058765
maximum_allowed_auroc_degradation=0.001
```

The candidate improves aggregate probability-quality metrics, but it degrades ranking discrimination by substantially more than the predeclared tolerance.

The replay therefore retained:

```text
failure_label=ranking_safety_regression
promotion_recommendation=KEEP_DIAGNOSTIC_ONLY
calibrator_promotion_status=not_authorized_ranking_safety_regression
```

SpecSafe must now close the promotion attempt explicitly. Leaving the candidate in an ambiguous retained-candidate state would allow future threshold, scheduler, or public-proof work to treat improved Brier/ECE as if the complete gate had passed.

## Decision

SpecSafe adopts the replay recommendation exactly:

```text
decision_outcome=KEEP_DIAGNOSTIC_ONLY
promotion_attempt_status=closed_not_promoted
candidate_disposition=retained_diagnostic_negative_evidence
calibrator_promotion_status=not_authorized_closed_ranking_safety_regression
automated_scheduling_confidence_status=unfit_use_conservative_fallback
```

The current candidate calibrator is not promoted and may not be used as trusted probability input for automated scheduling.

Its retained purpose is limited to:

```text
- reproducible diagnostic evidence
- a negative example of probability-quality improvement with ranking regression
- a regression fixture for future calibration methods
- bounded public explanation of why multi-metric promotion gates matter
```

## Decision Rules

### Rule 1: The complete gate controls promotion

Improved Brier score and fixed-bin ECE are necessary evidence, but they do not override a failed ranking-safety gate.

A candidate that compresses raw scores into repeated piecewise-constant probabilities can improve calibration metrics while reducing useful discrimination. Promotion requires the entire predeclared gate, not a favorable subset.

### Rule 2: Conservative fallback is mandatory

Any system path that would otherwise use this candidate's calibrated probability to automate scheduling must use a conservative fallback state instead.

This decision does not promote a threshold, scheduler, capacity policy, or adaptive-policy utility claim.

### Rule 3: The independent holdout is consumed evidence

The retained holdout may not be used to:

```text
- refit the current candidate
- tune calibrated thresholds
- tune scheduler logic
- become part of a future fit pool
- select a replacement method after repeatedly inspecting holdout outcomes
```

Any replacement calibrator requires a separate predeclared protocol, fresh fit evidence, and fresh independent promotion evidence.

### Rule 4: Public use is negative-evidence-only

The replay and closeout may be packaged publicly only when the non-promotion result is visible.

Permitted public framing:

```text
- the candidate improved aggregate calibration metrics
- the candidate failed ranking safety
- the gate prevented unsafe promotion
- the candidate remains diagnostic negative evidence
```

Forbidden public framing:

```text
- the candidate calibrator passed
- calibrated thresholds are safe
- scheduler utility is improved
- final positive proof is complete
- production behavior is proven
```

## Consequences

### Positive consequences

- Prevents metric cherry-picking.
- Converts a negative result into a durable reliability proof asset.
- Preserves the independent holdout from tuning leakage.
- Gives future calibration work a clear regression target.
- Demonstrates that SpecSafe's gates can reject an apparently improved candidate.

### Negative consequences

- The current candidate cannot advance scheduler research as trusted calibrated input.
- A replacement candidate requires a fresh protocol and fresh evidence.
- Positive public proof and production claims remain unavailable.

### Accepted trade-off

SpecSafe prefers a credible negative closeout over promoting a candidate that fails a predeclared safety gate.

## Authorized Work After This ADR

```text
- retain the current candidate as diagnostic negative evidence
- use conservative fallback for probability-driven automation
- publish a bounded negative-evidence package with explicit non-promotion labels
- design a new calibrator under a separate predeclared protocol
- collect fresh fit and independent holdout evidence for a future candidate
```

## Blocked Work

```text
- promote the current candidate calibrator
- tune or promote thresholds from the consumed holdout
- run or promote a scheduler using the current candidate as trusted probability
- claim adaptive-policy utility from the current candidate
- present public artifacts as positive promotion proof
- claim production speed, latency, throughput, cost, or serving readiness
```

## Claims Ledger

Claims permitted:

```text
- The candidate completed independent holdout replay without refit.
- Aggregate holdout Brier score and fixed-bin ECE improved.
- Holdout ranking safety regressed beyond the declared tolerance.
- The promotion attempt is closed and the candidate is not promoted.
- The result is retained as diagnostic negative evidence.
```

Claims forbidden:

```text
- The current candidate calibrator is promoted.
- The current calibrated probabilities are fit for automated scheduling.
- Any threshold or scheduler is promoted from the current holdout.
- Adaptive-policy utility improvement is proven.
- Public artifacts demonstrate positive promotion proof.
- Production speed, latency, throughput, cost, or serving readiness is proven.
```

## Next Safe Boundary

After this closeout, the next safe work is one of:

```text
- bounded negative-evidence packaging
- new-calibrator redesign governance under a fresh predeclared protocol
```

Neither path may reopen or tune against the consumed holdout.

## Final Judgment

The candidate improved two probability-quality metrics and still failed the complete promotion gate.

That is not wasted work. It is evidence that the gate is functioning.
