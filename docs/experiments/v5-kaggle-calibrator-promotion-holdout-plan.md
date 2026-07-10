# V5 Kaggle Candidate Calibrator Independent Holdout Replay Plan

## Purpose

This plan defines the next evidence slice after the combined Kaggle candidate-calibrator fit-pool replay diagnostic.

The current candidate calibrator passed replay on the same pool used to fit it. That is useful, but it is not independent promotion evidence.

This plan exists to produce an independent holdout replay decision without contaminating calibration parameters, thresholds, scheduler policy logic, capacity profiles, or public claims.

## Current Boundary

```text
current_boundary=post_combined_candidate_calibrator_fit_pool_replay
candidate_calibrator=v5-qwen-combined-fixed-bin-isotonic-calibrator-v1
current_status=retained_candidate
fit_pool_replay_status=passed
holdout_status=not_available_fit_pool_replay_only
calibrator_promotion_status=not_authorized_pending_independent_holdout
```

## Research Question

Can the retained candidate calibrator improve probability quality on independent holdout traces without relying on the fit pool?

## Evidence Class

```text
evidence_class=kaggle_environment_evaluated
evidence_role=independent_holdout_replay
production_serving_validated=false
public_replay_demo_released=false
```

## Data Role

The holdout archive has exactly one role:

```text
holdout evaluation
```

It must not be used for:

```text
- fitting calibrator parameters
- selecting calibrated thresholds
- changing scheduler policy logic
- changing capacity curves
- selecting prompts after outcomes are reviewed
- creating stronger claims before the frozen replay report exists
```

## Required Independence Boundary

The holdout material must be prompt/task-separated from:

```text
- v2 Kaggle trace collection fit material
- negative-case expansion fit material
- combined calibration diagnostic fit pool
- candidate calibrator fit pool
```

The holdout material must not be selected by looking at candidate calibrator errors from the fit pool and then constructing only favorable cases.

Hard negative and adverse cases are allowed only if the plan records them before outcomes are used for promotion.

## Inputs

Expected inputs for the holdout replay slice:

```text
- retained candidate calibrator artifact
- retained candidate calibrator manifest
- holdout prompt/task corpus or holdout trace archive
- holdout source manifest
- holdout runtime metadata
- replay configuration
```

## Outputs

Required retained outputs:

```text
- holdout trace archive
- holdout trace manifest
- deterministic holdout analysis report
- candidate calibrator holdout replay report
- machine-readable result JSON
- human-readable experiment report
```

## Minimum Report Fields

The replay report must retain:

```text
report_id
run_id
source_commit
created_at
calibrator_artifact_id
calibrator_artifact_hash
holdout_archive_id
holdout_archive_hash
holdout_record_count
holdout_positive_count
holdout_negative_count
coverage_by_workload
coverage_by_position
raw_brier_diagnostic
calibrated_brier_holdout_diagnostic
brier_delta
raw_fixed_bin_ece_diagnostic
calibrated_fixed_bin_ece_holdout_diagnostic
ece_delta
discrimination_metric
threshold_preview
failure_labels
promotion_recommendation
claims_permitted
claims_forbidden
```

## Replay Procedure

### Step 1: Freeze holdout plan

Before any holdout result is inspected, freeze:

```text
- holdout source rules
- prompt/task inclusion rules
- minimum record target
- minimum negative-count target or explicit justification
- replay metrics
- threshold preview values
- failure labels
- promotion recommendation rules
```

### Step 2: Collect or identify holdout traces

If fresh Kaggle collection is required, collect holdout traces under a new collection ID and retain:

```text
- model IDs and revisions
- tokenizer ID and revision
- notebook or script revision
- decoding configuration
- seed
- runtime metadata
- trace schema version
- export manifest
```

If an existing archive is used, prove it was not used for the candidate calibrator fit.

### Step 3: Validate archive and manifest

Reject the replay if:

```text
- archive hash mismatch exists
- required provenance is missing
- split role is ambiguous
- prompt/task independence is not documented
- labels or outcomes influenced calibrator fit or threshold selection
```

### Step 4: Run deterministic analysis

Produce summary counts before replay:

```text
- total records
- positives
- negatives
- workload counts
- position counts
- raw confidence distribution
- missing/invalid field counts
```

### Step 5: Replay retained candidate calibrator

Apply the retained candidate calibrator exactly as stored. Do not refit. Do not update bins. Do not tune thresholds.

### Step 6: Generate holdout replay report

The report must state:

```text
- whether replay passed deterministically
- whether calibration improved on holdout
- whether ranking safety was preserved
- whether coverage is sufficient
- whether promotion is recommended
- what claims remain forbidden
```

## Promotion Recommendation Values

Use one of these exact recommendation labels:

```text
PROMOTE_CANDIDATE_CALIBRATOR
KEEP_DIAGNOSTIC_ONLY
REQUIRE_ADDITIONAL_HOLDOUT_EVIDENCE
REJECT_CANDIDATE_CALIBRATOR
```

## Failure Labels

The report must support at least:

```text
holdout_manifest_mismatch
holdout_provenance_missing
holdout_split_leakage
holdout_negative_count_insufficient
holdout_coverage_insufficient
calibration_quality_regression
ranking_safety_regression
threshold_preview_sparse_support
calibrator_refit_detected
unsupported_promotion_claim
```

## Threshold Preview Rules

Threshold previews are allowed only as diagnostics.

They must not become threshold promotion evidence unless a separate threshold governance decision is made.

Required preview thresholds:

```text
0.50
0.60
0.70
0.80
0.90
0.95
```

Each threshold preview must include:

```text
selected_count
match_count
nonmatch_count
selection_rate
nonmatch_rate
coverage_warning
```

## Acceptance Criteria

This slice is successful only if:

```text
- independent holdout boundary is documented
- no refit path is authorized
- no threshold promotion is authorized
- no scheduler promotion is authorized
- replay report fields are predeclared
- failure labels are predeclared
- promotion recommendation labels are predeclared
- claims and non-claims are explicit
```

## Claims Permitted After This Plan

```text
- SpecSafe has a governed plan for independent candidate-calibrator holdout replay.
- The retained candidate calibrator remains diagnostic-only until holdout replay evidence exists.
```

## Claims Forbidden After This Plan

```text
- calibrator promotion
- threshold promotion
- scheduler promotion
- adaptive-policy utility improvement
- Hugging Face final public proof release
- production speed, latency, cost, throughput, or serving readiness
```

## Next Safe Implementation Slice

After this plan merges, the next safe slice is one of:

```text
- holdout prompt/task corpus and precollection manifest
- holdout archive retention if already collected
- holdout analysis/replay script and tests
```

Do not start Hugging Face final proof packaging before the holdout replay boundary is resolved.
