# Baseline Replay Evidence Ledger

## Purpose

This boundary produces a typed, local JSON ledger for the two causal baseline families:
fixed-length and static-threshold verification. It records exact immutable policy
configuration plus deterministic replay output over the controlled synthetic fixture set.

It is an evidence-retention boundary, not a policy-comparison report.

## Scope

The ledger includes only cases assigned to these governed splits:

- `development`;
- `adversarial_regression`.

It excludes `calibration` and `final_evaluation` by construction. In particular, the
held-out final-evaluation case is not selected, scored, inspected, or used to configure a
baseline policy through this API.

## Retained fields

Every ledger retains:

- schema version, ledger ID, and deterministic run ID;
- fixture-set ID and version;
- synthetic-controlled evidence classification;
- explicit `no_cross_policy_winner_claim` posture;
- typed fixed-length or static-threshold policy configuration;
- one valid replay result for each policy/case pair;
- retained decisions, post-hoc outcome joins, terminal state, and processed/unprocessed
  counts already validated by the replay boundary.

The policy configuration is retained because a policy ID by itself is insufficient
provenance. For example, two fixed-length policies may share an implementation family while
using different verification budgets.

## Validity and causal boundary

The ledger accepts only `FixedLengthVerificationPolicy` and
`StaticThresholdVerificationPolicy`. Each entry is produced through
`run_valid_policy_replay(...)`, which supplies a policy only one
`CausalSchedulerContext` at a time and attaches outcomes after retaining a decision.

An evaluation-only retrospective policy is rejected before a ledger is built. The unsafe
control remains available only in its separate negative-control replay path and cannot enter
a valid baseline ledger.

## No winner claim

The ledger contract intentionally has no fields for utility, ranking, score, comparison
result, or `winner_policy_id`.

This prevents the ledger from being treated as evidence that one baseline wins. A later
comparison requires a declared utility function, calibrated-confidence evidence, capacity
profile provenance, split discipline, and a report that preserves neutral or negative cases.

## Determinism and persistence

With the same immutable fixture set, policy configurations, ledger ID, and run ID, ledger
construction is deterministic. `write_baseline_replay_evidence_ledger_json(...)` serializes a
specified ledger to an explicit local `.json` destination using an adjacent temporary file
then replace operation. It does not modify source fixtures or manifests.

## Current non-claims

This boundary does not fit calibration, select thresholds, model capacity, calculate utility,
assign a baseline winner, compare policies, use final-evaluation data, run Kaggle experiments,
or establish production performance.
