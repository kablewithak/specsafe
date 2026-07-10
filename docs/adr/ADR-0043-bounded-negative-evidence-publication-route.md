# ADR-0043: Select Bounded Negative-Evidence Packaging Before Any New Calibrator Programme

## Status

Accepted.

## Date

2026-07-10

## Context

The current Kaggle-derived candidate calibrator completed an independent no-refit holdout replay.
It improved aggregate Brier score and fixed-bin ECE but regressed AUROC beyond the predeclared
ranking-safety tolerance.

The promotion attempt is formally closed:

```text
decision_outcome=KEEP_DIAGNOSTIC_ONLY
promotion_attempt_status=closed_not_promoted
candidate_disposition=retained_diagnostic_negative_evidence
automated_scheduling_confidence_status=unfit_use_conservative_fallback
```

The closeout authorizes two broad future directions:

1. package the result publicly as bounded negative evidence; or
2. charter a genuinely new calibrator under a separate protocol with fresh fit and holdout evidence.

The repository has already completed the controlled synthetic policy-comparison proof and a
substantial Kaggle evidence-acquisition programme. Automatically starting another calibrator cycle
would risk converting the project into an open-ended calibration search and would delay the public
proof and final reconciliation boundaries.

## Decision

SpecSafe will next build a deterministic local **bounded negative-evidence release pack**.

The pack will present the candidate rejection as the primary reliability result:

```text
probability_quality_improved=true
ranking_safety_passed=false
promotion_blocked=true
conservative_fallback_required=true
```

A fresh calibrator redesign is deferred. It requires a separate future ADR and may not begin as an
implicit continuation of the closed candidate programme.

## Why this route is preferred

### It advances the project toward completion

The public proof layer is an explicit project deliverable. The repository now has enough retained
evidence to demonstrate not only how a candidate is evaluated, but how an apparently favorable
candidate is rejected when a higher-priority safety gate fails.

### It avoids metric-shopping

Starting another method immediately after seeing the consumed holdout result would create pressure
to choose a method against known outcomes. The bounded release route preserves the result rather
than optimizing it away.

### It demonstrates harness value

The strongest proof is not that every candidate passes. It is that the harness can:

- preserve independent evidence;
- enforce no-refit boundaries;
- calculate declared metrics;
- detect a ranking regression;
- block promotion;
- retain a conservative fallback;
- publish a bounded claim ledger.

### It keeps the project local-first

The next implementation produces a deterministic local release directory and manifest. It does not
require Hugging Face credentials, hosted model inference, deployment infrastructure, or secrets.

## Required contents of the release pack

The local pack must contain only sanitized, precomputed artifacts:

- a machine-readable release summary;
- a release manifest with SHA-256 hashes and byte counts;
- a dataset-card-style README;
- an evidence-boundary page;
- aggregate candidate and holdout metrics;
- explicit failure labels;
- permitted claims and forbidden claims;
- reproduction instructions using committed local artifacts.

The pack must not contain:

- raw prompt text;
- raw private or customer data;
- retained Kaggle archive ZIPs;
- secrets or environment dumps;
- raw logits;
- hidden threshold selection;
- a promoted scheduler configuration;
- production or serving claims.

## Required validity marker

The release must display:

```text
CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY
```

It must not headline a utility or promotion success.

## Source integrity requirements

The builder must fail closed unless the retained source artifacts match their expected hashes and
states, including:

- the independent holdout replay report;
- the promotion closeout decision;
- the candidate artifact identity;
- the consumed holdout identity;
- `KEEP_DIAGNOSTIC_ONLY`;
- `closed_not_promoted`;
- `ranking_safety_regression`;
- conservative fallback status.

## Publication boundary

This ADR authorizes local package construction only.

Actual publication remains blocked until a separate review confirms:

- exact release-pack bytes and hashes;
- sanitization and allowlist compliance;
- license selection;
- dataset card accuracy;
- prominent non-promotion labels;
- no secret-dependent or live model inference;
- no user-input retention;
- no unsupported positive proof claim.

## Fresh calibrator boundary

Any future candidate must begin with a separate predeclared protocol that fixes, before evidence is
collected or inspected:

- the new research question;
- the method family and parameter boundary;
- fit evidence rules;
- independent holdout rules;
- minimum coverage;
- probability-quality gates;
- ranking-safety gates;
- stop conditions;
- consumed-evidence prohibitions;
- promotion and non-promotion labels.

The current holdout may not be reused to choose or tune that method.

## Consequences

### Positive

- Advances public proof without overclaiming.
- Preserves the negative result as valuable evidence.
- Demonstrates a real promotion gate and fallback path.
- Prevents automatic calibrator iteration.
- Keeps public packaging deterministic and provider-neutral.

### Negative

- Does not produce a promoted Kaggle-derived calibrator.
- Does not unlock threshold or scheduler promotion.
- Requires a later explicit publication review.
- Leaves any successor-calibrator programme for a separate decision.

## Next implementation slice

```text
branch=feat/bounded-negative-evidence-release-pack
scope=local deterministic sanitized release-pack builder, retained pack, tests, and documentation
actual_publication=false
```
