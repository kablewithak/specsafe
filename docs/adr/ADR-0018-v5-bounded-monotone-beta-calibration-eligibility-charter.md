# ADR-0018: Constitute V5 as a Bounded Monotone-Beta Calibration Eligibility Programme

- **Status:** Accepted
- **Date:** 2026-07-07
- **Decision owner:** Kabo Molefe
- **Applies to:** `synthetic-calibration-successor-v5`
- **Depends on:** ADR-0001, ADR-0002, ADR-0015, ADR-0016, and ADR-0017
- **Supersedes:** No historical calibration result. It creates a new, isolated V5 programme.

## Context

SpecSafe has completed the reusable causal, baseline, deterministic replay, and evidence-retention
foundation required for the north-star proof. ADR-0017 confirms that the missing route is now:

```text
fresh calibration eligibility
  -> causal load-aware adaptive policy
  -> declared capacity profiles
  -> same-input shared scoring and comparison
```

V4 is closed. Its held-out result improved Brier score and ECE but failed the independent
ranking-safety gate. ADR-0016 therefore blocks every V4 refit, rerun, policy comparison,
scheduler, capacity-policy, and runtime-control path.

The project must not respond by iterating indefinitely through calibration methods. A successor
is justified only because an eligible confidence path is required before the core adaptive-policy
proof can begin. The successor must be fixed before fresh case assets exist, must retain the
ranking-safety requirement, and must have an explicit stop rule.

## Decision

SpecSafe will run one fresh, bounded **V5 calibration eligibility programme**.

V5 answers one narrow question only:

> Can one predeclared, strictly monotone calibration transform meet the complete held-out
> probability-quality and ranking-safety gate on fresh synthetic evidence?

V5 does **not** implement or evaluate an adaptive scheduler, capacity profile, policy utility
scorer, cross-policy comparator, Kaggle experiment, or public replay release.

### 1. V5 evidence isolation

V5 must use a new evidence root and new case namespace:

```text
fixture_set_id=synthetic-calibration-successor-v5
fixture_root=data/fixtures/synthetic_calibration_successor_v5/

calibration_case_range=CSV5-101..CSV5-148
final_evaluation_case_range=CSV5-201..CSV5-236
adversarial_regression_case_range=CSV5-301..CSV5-312
```

The following are prohibited as V5 method-selection, fitting, threshold, fixture-design, or
final-interpretation inputs:

```text
all V1, V2, V3, and V4 held-out runtime inputs
all V1, V2, V3, and V4 held-out outcomes and labels
all historical final metric values
all historical calibrator parameter values and fitted artifacts
all historical final case IDs, scenario-family fingerprints, and case-level patterns
all historical policy-configuration, capacity-cost, or score-selection values
```

Historical programmes may contribute only durable process controls:

```text
separate calibration and final evidence
strict causal boundary
manifest and provenance verification
ranking safety as an independent gate
write-once final persistence
no refit during final assessment
no policy execution during calibration assessment
conservative fallback
```

### 2. Fixed V5 method

V5 selects one calibration method before V5 fixtures, calibration labels, or final outcomes exist:

```text
artifact_id=bounded-monotone-beta-calibration-v5
artifact_version=1.0.0
method_family=global_monotone_beta_calibration
fit_split=calibration
fit_data_role=calibration
runtime_control_eligible=false
```

For a raw conditional-survival confidence `p`, V5 computes:

```text
p_clipped = min(max(p, 0.000001), 0.999999)
logit(q) = a * log(p_clipped) - b * log(1 - p_clipped) + c
q = sigmoid(logit(q))
```

The parameters are globally shared and frozen as follows:

| Setting | Fixed V5 value |
|---|---|
| `a` bound | `[0.25, 4.00]` |
| `b` bound | `[0.25, 4.00]` |
| `c` bound | `[-4.00, 4.00]` |
| Initialization | `a=1.0`, `b=1.0`, `c=0.0` |
| Objective | Mean binary negative log likelihood plus `0.02 * ((a - 1)^2 + (b - 1)^2 + c^2)` |
| Optimizer | `deterministic_projected_gradient_descent_v1` |
| Learning rate | `0.02` |
| Maximum iterations | `8000` |
| Objective tolerance | `0.000000000001` |
| Gradient-norm tolerance | `0.00000001` |
| Confidence clipping epsilon | `0.000001` |
| Equal-objective tie rule | Retain the earlier iteration |

The positive lower bounds for `a` and `b` make the transform strictly increasing in exact
arithmetic. This is a design property, not a promotion claim. V5 must still calculate and retain
its tie-aware AUROC result on the final assessment because finite values, repeated inputs, and
implementation defects can still produce an unsafe recorded result.

V5 must not add workload-specific, position-specific, request-specific, capacity-specific, or
scenario-specific parameters. It must not use a candidate-method tournament, cross-programme
model selection, or post-label method replacement.

### 3. Fresh corpus constitution

V5 has three separate roles:

| Role | Cases | Positions per case | Observations | Allowed use |
|---|---:|---:|---:|---|
| Calibration | 48 | 4 | 192 | Fit only the frozen V5 artifact. |
| Final evaluation | 36 | 4 | 144 | One write-once held-out calibration gate only. |
| Adversarial regression | 12 | 4 | 48 | Future regression protection only; never fitting or threshold selection. |

Each role must contain self-authored, public-safe cases across:

```text
structured_text
code
open_ended_chat
```

The calibration and final corpora must each include fixed scenario families for:

```text
confidence-curve coverage
candidate-position spread
workload variation
local mixed-reliability contrast
```

These family names describe diagnostic responsibilities, not a permission to copy historical case
content or case patterns. Exact runtime inputs, expected outcomes, manifests, and provenance
hashes must be new V5 assets.

### 4. Required implementation order

V5 must proceed in this order:

```text
V5-0  ADR-0018 merged
V5-1  typed V5 artifact, result, manifest, and error contracts
V5-2  non-final final-assessment harness and deterministic regression tests
V5-3  calibration fixtures and immutable calibration manifest
V5-4  calibration-only fit and diagnostics; frozen V5 artifact
V5-5  final fixtures and immutable final manifest/evidence index
V5-6  one write-once V5 final held-out calibration assessment
V5-7  close V5 as eligible or negative
```

Before V5-2 is merged, V5 must not author V5 runtime inputs, labels, manifests, calibration
artifacts, final assets, or policy code.

Before V5-5 is merged, V5 must not author V5 final runtime inputs or outcomes.

Before V5-6 is run, the V5 final-assessment contract and non-final tests must prove complete
gate semantics without loading V5 final evidence.

### 5. V5 held-out calibration eligibility gate

The V5 final assessment must retain raw and calibrated metrics, all provenance fields, all gate
booleans, the final status, and a canonical result hash. It passes only when every condition below
is true.

| Gate | Required V5 condition |
|---|---|
| Manifest integrity | Every final runtime, outcome, and evidence-index asset matches its declared hash and byte count. |
| Provenance alignment | The frozen artifact identifies the V5 calibration manifest only; the final evaluator identifies the V5 final manifest only. |
| Observation coverage | Exactly 36 final cases and 144 final observations are loaded. |
| Position coverage | Each candidate position has exactly 36 final observations. |
| Workload coverage | Each required workload class has exactly 48 final observations. |
| Monotonicity verification | The frozen artifact passes deterministic monotonicity checks on declared boundary and observed calibration inputs. |
| Brier improvement | `raw_brier - calibrated_brier >= 0.005000000000`. |
| ECE improvement | `raw_ece_10_bin - calibrated_ece_10_bin >= 0.010000000000`. |
| Ranking safety | `calibrated_auroc - raw_auroc >= -0.001000000000`. |
| No refit | No fit, parameter mutation, threshold selection, or mapping replacement occurs during final assessment. |
| No policy execution | No baseline, scheduler, capacity-profile, utility, replay comparison, or runtime action executes during the calibration assessment. |
| Write-once precheck | A pre-existing final-result destination is rejected before any final evidence is loaded. |
| Canonical serialization | Equivalent approved non-final result objects serialize byte-identically. |

Permitted final statuses are:

```text
PASSES_V5_CALIBRATION_ELIGIBILITY_GATE
CALIBRATOR_REGRESSION
RANKING_SAFETY_REGRESSION
INSUFFICIENT_HELD_OUT_COVERAGE
INVALID_PROVENANCE
INCOMPLETE_GATE_EVIDENCE
WRITE_ONCE_DESTINATION_EXISTS
```

A pass yields only:

```text
adaptive_policy_research_eligibility=eligible_for_controlled_policy_research
runtime_control_eligible=false
```

A non-passing result yields:

```text
adaptive_policy_research_eligibility=blocked
runtime_control_eligible=false
fallback=CONSERVATIVE_FALLBACK
fallback_policy_id=fixed-short-1-v5
```

The declared fallback is a future fixed-length configuration with a maximum verification length of
one. It is not a deployment recommendation and it does not authorize V5 policy comparison.

### 6. Explicit stop rule

V5 is the final automatic successor-calibration route in the current SpecSafe plan.

If V5 does not pass its complete held-out calibration eligibility gate:

1. V5 closes as retained negative evidence.
2. No V6 calibration redesign, parameter sweep, method tournament, final rerun, threshold
   adjustment, or fixture rebalance is automatically authorized.
3. The project returns to a formal owner decision: either retire the adaptive-policy thesis and
   package the existing reliability foundation, or approve a materially different research
   question through a new PRD/ADR decision.
4. The V5 final corpus, artifact, manifests, and result become audit-only historical evidence.

If V5 passes, it authorizes only the next local proof design:

```text
capacity-profile contract
+ causal adaptive-policy contract
+ shared utility scorer
+ same-input comparison contract and tests
```

A V5 pass does not authorize live runtime control, production claims, Kaggle work, public demo
work, or an adaptive-policy advantage claim.

### 7. Prohibited work in this ADR slice

This ADR does not authorize:

```text
V5 fixture authoring
V5 calibration fitting
V5 final-evaluation authoring
V5 final assessment
V5 scheduler implementation
V5 capacity-profile implementation
V5 policy utility scoring
V5 baseline or adaptive policy comparison
V5 Kaggle work
V5 Hugging Face publication
any V4 modification
```

## Alternatives considered

| Alternative | Decision | Reason |
|---|---|---|
| Repair, smooth, or rerun V4 | Rejected | V4 final evidence is consumed and ADR-0016 prohibits remediation in place. |
| Rebuild the existing fixed/threshold baselines | Rejected | ADR-0017 confirms the baseline and replay foundation is already implemented. |
| Build the scheduler before calibration eligibility | Rejected | A probability-driven adaptive intervention is not authorized without a passing gate. |
| Run a V5 method tournament | Rejected | It would add selection complexity and invite method churn before the core proof. |
| Select a global strictly monotone beta calibration method | Accepted | It is deterministic, globally bounded, more expressive than temperature or two-parameter Platt scaling, and preserves ordering by design while retaining an independent final ranking gate. |
| Skip V5 and retire the adaptive thesis immediately | Rejected for now | One final bounded attempt is justified by the unresolved north-star proof, but only under the hard stop rule above. |

## Consequences

### Positive

- The next work is finite and auditable rather than another open-ended calibration loop.
- The calibration transform is globally shared, bounded, deterministic, and rank-preserving by
  mathematical construction.
- V5 separates calibration eligibility from the later policy-value claim.
- A passing V5 route has a direct next technical boundary: capacity, adaptive-policy, and shared
  comparison contracts.

### Costs and risks

- V5 may fail its held-out gate, ending automatic calibration iteration for the current plan.
- Strict monotonicity does not guarantee better probability quality.
- Better Brier/ECE values would still not prove adaptive policy value.
- The project remains below `held-out replay evaluated` until a later valid same-input policy
  comparison is retained.

## Claims after this ADR

### Permitted

- SpecSafe has a bounded V5 calibration eligibility constitution with a fresh namespace, fixed
  method, full held-out gate, conservative fallback, and hard stop rule.
- V5 uses a strictly monotone bounded beta calibration transform by design.
- V5 has not authored data, fitted an artifact, run a final assessment, or evaluated a policy.

### Forbidden

- V5 calibration improves any metric.
- V5 is eligible for adaptive policy research.
- A causal adaptive scheduler exists or has been evaluated.
- A policy utility winner exists.
- Kaggle, public replay, serving, throughput, latency, cost, or production evidence exists.

## Acceptance criteria

This decision is complete only when:

- this ADR is merged on `main`;
- `README.md` and `docs/PRD.md` state that V5 is chartered but pre-fixture;
- no source, tests, V5 fixture assets, manifests, artifacts, or results are added;
- no V1–V4 evidence bytes, manifests, artifacts, or results are modified;
- no scheduler, capacity profile, utility scorer, or comparison code is added;
- `main` is clean after merge.

## Final control statement

> V5 is one bounded eligibility attempt, not a permission to keep searching until a calibrator
> looks good. It either produces a complete, rank-safe calibration gate that permits controlled
> policy research, or it closes and forces an explicit strategic decision.
