# ADR-0004: Establish a Fresh Calibration Fixture-Set Boundary

- **Status:** Accepted for governance; implementation not yet authorized
- **Date:** 2026-07-02
- **Decision type:** Evidence, split, and provenance boundary
- **Supersedes:** None
- **Related decisions:**
  - `ADR-0002-causal-information-boundary.md`
  - `ADR-0003-calibration-redesign-boundary.md`
- **Governing sources:** `docs/PRD.md`, accepted ADRs, committed contracts, fixtures,
  tests, and current terminal evidence

## Context

SpecSafe completed Phase 3 calibration assessment with a retained negative result.
The equal-width histogram calibrator was fitted on calibration-only assets and later
assessed against the governed final-evaluation fixture `STF-004`. It regressed against
raw confidence and was correctly not promoted.

ADR-0003 established the immediate remediation rule:

```text
Do not tune, refit, or otherwise optimize the current calibrator against STF-004.
```

That rule alone is not enough. A future calibration attempt needs a fresh, inspectable
fixture boundary before any new evidence is authored. Without one, new cases could
accidentally reuse the consumed held-out scenario, share latent templates across splits,
or silently turn the final-evaluation set into an optimization target.

This ADR establishes the governed design boundary for a new synthetic calibration
fixture set. It does not create fixtures, alter manifests, add calibrator code, change
policy behavior, or authorize adaptive scheduling.

## Decision

The next calibration-evidence implementation shall use a new fixture-set identity:

```text
fixture_set_id=synthetic-calibration-redesign-v1
fixture_set_version=1.0.0
fixture_set_status=proposed_until_implemented_and_manifest_verified
source_type=synthetic
```

The implementation must follow the companion document:

```text
docs/architecture/fresh-calibration-fixture-set-proposal.md
```

### 1. `STF-004` remains permanently quarantined from redesign work

`STF-004` is historical held-out evidence for the prior calibrator only. It must not be
used for any of the following:

- calibration-method selection;
- parameter, bin, or threshold selection;
- synthetic scenario selection;
- fixture-shape selection;
- expected-outcome selection;
- comparative calibration validation;
- regression tuning;
- promotion review for the redesigned artifact.

The prior negative result may be cited only as a reason to require a fresh protocol. It
must not be mined for numeric or scenario-level optimization clues.

### 2. Split separation occurs at the scenario-family level

The new fixture set must reserve distinct scenario families for each role:

```text
development
calibration
final_evaluation
adversarial_regression
```

A scenario family, source template, prompt skeleton, or parent scenario identity used
for `calibration` must not also appear in `final_evaluation`, including renamed,
truncated, reordered, or lightly perturbed variants.

The same rule applies in reverse. A final-evaluation scenario family cannot be copied
into calibration or development after its outcomes are reviewed.

### 3. Runtime inputs and expected outcomes remain structurally separate

The fixture layout must preserve the existing causal and evaluation boundaries:

```text
inputs/cases/
expected_outcomes/
manifest.json
```

Runtime-input files contain only typed information lawful for fixture loading and
subsequent causal-policy replay. Expected-outcome files contain labels and post-hoc
calibration observations. A runtime input must not embed observed acceptance labels,
future-derived values, or retrospective optimal-prefix data.

### 4. The fixture protocol is frozen before artifact fitting

Before the new calibrator is fitted:

- the scenario-family registry must be committed;
- each family must have a single declared split and data role;
- manifest rules and required provenance fields must be committed;
- the candidate method must remain the ADR-0003 predeclared method;
- the promotion criteria must remain predeclared;
- the new final-evaluation families must be identified but not used to tune the method.

### 5. Fixture authoring does not imply promotion

A valid fixture set proves only that a fresh evidence boundary exists. It does not prove:

- that `logit-temperature-scaling-v1` improves calibration;
- that confidence is fit for automated scheduling;
- that a causal adaptive scheduler is authorized;
- that a policy utility comparison exists;
- any production-serving, throughput, latency, cost, or losslessness claim.

## Consequences

### Positive consequences

- Prevents the consumed held-out fixture from becoming a tuning target.
- Makes split leakage detectable through a named scenario-family registry.
- Preserves a clear runtime-input versus expected-outcome boundary.
- Gives a future fixture implementation a testable, reviewable contract.
- Preserves the credibility of any later held-out calibration result.

### Costs and constraints

- More fixture authoring and provenance discipline are required before code changes.
- A new final-evaluation split cannot be created casually after inspecting calibration
  results.
- The next calibrator may still fail. That negative result must also be retained.
- The project remains blocked from adaptive-policy implementation until a fresh frozen
  artifact passes its separate promotion gate.

## Alternatives considered

### A. Retune the existing histogram calibrator using `STF-004`

Rejected. This would convert the prior held-out assessment into a tuning loop and
invalidate the independence of the retained negative result.

### B. Create a new fixture set without scenario-family provenance

Rejected. File-level split labels alone do not prevent near-duplicate or lineage-based
leakage across calibration and final-evaluation assets.

### C. Start adaptive-policy implementation with the current failed calibrator

Rejected. The current promotion gate is explicitly blocked. Better policy code cannot
repair an unfit or unpromoted confidence artifact.

### D. Use external or customer-derived data to accelerate evidence collection

Rejected for this slice. SpecSafe remains synthetic and public-safe at this boundary.
No customer, private, or sensitive data is authorized.

## Implementation requirements for the next slice

The subsequent fixture implementation slice must include all of the following together:

1. New runtime-input case assets and structurally separate expected-outcome assets.
2. A scenario-family registry with one declared split per family.
3. A manifest containing file hashes, byte counts, split counts, source type, and
   scenario-family inventory.
4. Loader and manifest validation tests.
5. Regression tests that reject family/template reuse across calibration and
   final-evaluation splits.
6. Documentation updates needed to identify the new fixture set as synthetic,
   calibration-redesign evidence only.

No calibration fitting, final-evaluation assessment, adaptive scheduling, capacity
profile, or policy-utility implementation belongs in that fixture-authoring slice.

## Verification for this ADR slice

This is a documentation-only governance decision. Required verification is limited to:

```text
git status
git diff --check
```

No pytest or Ruff run is required unless an executable file changes.

## Non-claims

This ADR does not claim calibration improvement, policy improvement, empirical model
behavior, public release readiness, or production readiness.
