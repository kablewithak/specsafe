# Calibration Redesign V3 Entry Gate

## Purpose

This document prevents a rushed V3 retry after the V2 negative result.

V3 is not authorized by this document. It describes what must be decided and recorded before any V3 runtime case, outcome file, manifest, fitter, or test expectation is created.

## Starting point

V2 is closed.

```text
v2_status=closed_negative_result
v2_candidate=bounded-platt-scaling-v1
v2_promotion=not_promoted_calibrator_regression
v2_scheduler_research=blocked
```

V3 must not be framed as “make V2 pass.” It must be a new controlled experiment.

## Required V3 decision record

Before V3 evidence exists, create and accept a V3 entry ADR that states:

1. **Fresh question** — what V3 is testing that is different from V2.
2. **One candidate approach** — one bounded method or design, chosen before V3 labels exist.
3. **Why the approach is allowed** — based on its form, simplicity, safety, and reproducibility, not V2 numbers or case patterns.
4. **Fresh evidence plan** — separate V3 development, calibration, final-evaluation, and adversarial-regression roles.
5. **Fresh success gate** — fixed metrics, minimum evidence size, and failure response written before V3 outcomes exist.
6. **No-claim boundary** — what a V3 result would still not prove.

## V2 quarantine rule

V2 can be used only as the categorical historical fact that its frozen candidate was not promoted.

V3 must not use V2 data-bearing material to choose a method, choose a threshold, choose a fixture shape, choose a sample size, choose an acceptance rule, or write test expectations.

Forbidden V2 inputs include:

```text
confidence values
acceptance labels
prefix-survival labels
case IDs
trace IDs
candidate token IDs
fixture text or sequence shapes
manifest hashes
metric values
bin counts
artifact parameters
fit iterations
hidden-test outcomes
assessment report details
```

## Minimum V3 evidence discipline

V3 must preserve the same core safety structure:

```text
method decision before V3 data
-> separately stored runtime inputs and outcomes
-> calibration-only manifest
-> frozen fit
-> separate hidden-test manifest
-> one read-only assessment
-> retain the result
```

## Stop conditions

Do not start V3 if the proposed work does any of the following:

- changes only the V2 method strength in response to V2 hidden results;
- reuses V2 case shapes or labels as “inspiration” for V3 fixtures;
- adds more flexible parameters without a new evidence plan;
- makes scheduler claims before a V3 held-out calibration result;
- treats a V3 fit improvement as proof of hidden-test success;
- starts V3 mainly to erase an uncomfortable V2 result.

## Next safe action

The next action is a design review, not code:

```text
Decision: close project at V2 as a strong negative-result proof artifact,
or approve a fresh V3 entry ADR with a genuinely new question.
```

No branch name, implementation plan, or V3 asset path is authorized until that decision is made.
