# ADR-0041: Candidate Calibrator Promotion Requires Independent Holdout Replay

## Status

Accepted

## Date

2026-07-10

## Context

SpecSafe has reached the post combined Kaggle candidate-calibrator fit-pool replay boundary.

The current retained candidate calibrator is:

```text
model_id=v5-qwen-combined-fixed-bin-isotonic-calibrator-v1
calibrator_type=fixed_bin_laplace_isotonic_v1
input_feature=raw_confidence
output_feature=calibrated_acceptance_probability
fit_records=184
fit_positives=148
fit_negatives=36
calibrator_fit_status=fit_retained
calibrator_promotion_status=not_authorized
```

The combined evidence pool crossed the earlier negative-count blocker:

```text
combined_records=184
combined_matches=148
combined_nonmatches=36
minimum_negative_floor=30
negative_count_floor_crossed=true
```

The candidate calibrator replay passed on the same fit pool:

```text
fit_pool_replay_records=184
fit_pool_replay_positives=148
fit_pool_replay_negatives=36
calibrator_replay_status=fit_pool_replay_passed
holdout_status=not_available_fit_pool_replay_only
calibrator_promotion_status=not_authorized_no_holdout
```

The fit-pool replay is useful evidence for artifact reproducibility, report determinism, and basic transform behavior. It is not independent evidence of generalization.

A fit-pool replay can look strong because the calibrator was fitted on the same pool being replayed. Promoting the calibrator, threshold, or scheduler from this evidence would weaken SpecSafe's central evidence discipline.

The governing PRD requires calibration to be evaluated on held-out final evidence before confidence can safely drive automated scheduling. It also requires reports to separate valid results from invalid or unsupported claims, preserve evidence boundaries, and avoid production or serving claims from synthetic or Kaggle-only evidence.

## Decision

SpecSafe will require independent holdout replay before any candidate calibrator can be promoted beyond diagnostic status.

The retained candidate calibrator remains:

```text
calibrator_status=retained_candidate
calibrator_use=diagnostic_and_holdout_replay_candidate_only
calibrator_promotion_status=not_authorized_pending_independent_holdout
```

The following actions are not authorized from fit-pool replay evidence alone:

```text
- calibrator promotion
- threshold promotion
- scheduler promotion
- adaptive-policy utility claims
- Hugging Face final public proof release
- production speed, latency, cost, throughput, or serving-readiness claims
```

The next evidence gate is an independent holdout replay diagnostic using frozen, prompt/task-separated material that did not influence:

```text
- calibrator fit parameters
- calibrated threshold selection
- scheduler policy logic
- capacity-profile design
- prompt selection after outcome review
- public claims
```

## Decision Rules

### Rule 1: Fit-pool replay is diagnostic-only

Fit-pool replay may support these claims:

```text
- the retained calibrator artifact can be loaded and replayed deterministically
- the retained calibrator produces the expected in-sample diagnostic report
- the reporting path preserves status, provenance, and non-claim markers
```

Fit-pool replay may not support these claims:

```text
- the calibrator generalizes
- calibrated thresholds are safe
- scheduler utility is improved
- public release proof is complete
- production behavior is known
```

### Rule 2: Holdout replay must be independent

A valid holdout replay must use a holdout evidence pool whose prompts/tasks and outcomes did not influence the retained candidate calibrator or any promotion threshold.

The holdout plan must explicitly record:

```text
- holdout evidence role
- prompt/task-level split boundary
- source manifest
- trace archive identity
- model/tokenizer/environment provenance
- calibration artifact identity
- replay configuration identity
- result artifact identity
- non-claims
```

### Rule 3: Promotion is a separate decision

A passing holdout replay does not automatically promote:

```text
- calibrated thresholds
- scheduler policies
- capacity-aware utility claims
- public hosting claims
```

A separate promotion decision must inspect the holdout replay result, failure labels, coverage, calibration metrics, threshold behavior, and residual risk.

### Rule 4: Scheduler work remains blocked

No scheduler utility claim may use the retained candidate calibrator until the project has:

```text
- independent holdout replay evidence
- explicit calibrator promotion status
- a governed threshold decision or fallback boundary
- identical immutable traces for valid policy comparison
- causal-safety status in the comparison report
```

### Rule 5: Hugging Face release waits for the evidence boundary

The Hugging Face Dataset and Space may be planned, but final public proof packaging must not imply calibrator or scheduler promotion before the holdout boundary is resolved.

A precomputed replay Space is allowed only after the evidence maturity and non-claims are displayed clearly.

## Consequences

### Positive consequences

- Prevents in-sample diagnostics from becoming inflated public proof.
- Preserves the causal and split-discipline posture that makes SpecSafe credible.
- Keeps Hugging Face hosting from becoming a premature demo layer.
- Creates a clean governance seam before threshold and scheduler work.
- Makes the final case study easier to defend to engineers and CTOs.

### Negative consequences

- Adds at least one more evidence slice before public proof packaging.
- Delays scheduler-promotion and threshold-promotion work.
- Requires another governed holdout replay before the calibrator can be treated as more than a retained candidate.

### Accepted trade-off

The delay is worth it. The project's value is evidence discipline. A faster path that promotes from fit-pool replay would be weaker engineering.

## Allowed Work After This ADR

The following work is authorized after this ADR merges:

```text
- prepare independent holdout replay plan
- author or identify holdout collection material under a frozen plan
- collect holdout evidence if not already available
- retain holdout trace archive and manifest
- analyze holdout archive deterministically
- replay retained candidate calibrator on independent holdout
- produce holdout replay report with promotion recommendation
```

The following work remains blocked:

```text
- calibrator promotion
- threshold promotion
- scheduler promotion
- final Hugging Face proof packaging
- production or serving claims
```

## Required Holdout Replay Output

The holdout replay report must include:

```text
- report_id
- run_id
- source_commit
- calibrator_artifact_id
- calibrator_artifact_hash
- holdout_trace_archive_id
- holdout_trace_archive_hash
- holdout_record_count
- holdout_positive_count
- holdout_negative_count
- coverage_by_workload
- coverage_by_position
- raw_brier_diagnostic
- calibrated_brier_holdout_diagnostic
- brier_delta
- raw_fixed_bin_ece_diagnostic
- calibrated_fixed_bin_ece_holdout_diagnostic
- ece_delta
- discrimination_metric
- threshold_preview
- failure_labels
- promotion_recommendation
- claims_permitted
- claims_forbidden
```

## Promotion Criteria

The first holdout replay may recommend promotion only if all of the following are true:

```text
- holdout provenance is complete
- holdout evidence is independent from the fit pool
- no manifest/hash mismatch exists
- minimum holdout negative coverage is satisfied or explicitly justified
- calibrated probability quality improves or remains within the declared tolerance
- ranking safety does not regress beyond the declared tolerance
- threshold preview does not hide sparse-bin or coverage failure
- report states non-claims clearly
```

If these are not satisfied, the candidate calibrator remains retained diagnostic evidence.

## Claims Ledger

Claims permitted after this ADR:

```text
- SpecSafe has a retained candidate calibrator.
- The candidate calibrator passed fit-pool replay.
- The project has adopted an independent-holdout requirement before promotion.
- Fit-pool replay is diagnostic-only.
```

Claims forbidden after this ADR:

```text
- the candidate calibrator is promoted
- thresholds are promoted
- the scheduler is promoted
- calibrated scheduling utility is proven
- public proof release is complete
- production speed, latency, cost, throughput, or serving readiness is proven
```

Evidence required before stronger claims:

```text
independent holdout replay report with complete provenance, calibration diagnostics, threshold preview, failure labels, and explicit promotion recommendation
```

Residual uncertainty:

```text
Whether the retained candidate calibrator generalizes to independent holdout evidence.
```

## Compliance and Publication Controls

The holdout replay path must preserve:

```text
- public or self-authored prompts only
- no secrets
- no PII
- no private prompts
- no customer data
- no raw sensitive payloads
- minimized trace fields
- explicit source and license notes where relevant
```

## Final Judgment

Promoting a calibrator from fit-pool replay would turn a useful diagnostic into an overclaim.

SpecSafe will keep the current candidate calibrator as retained diagnostic evidence until independent holdout replay either supports promotion or preserves the candidate as a bounded negative/diagnostic artifact.
