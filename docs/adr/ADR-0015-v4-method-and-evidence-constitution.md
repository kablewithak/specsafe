# ADR-0015: Freeze the V4 Method and Evidence Constitution Before V4 Data Exists

- **Status:** Accepted
- **Date:** 2026-07-06
- **Decision owner:** Kabo Molefe
- **Applies from:** `main` after ADR-0014 is merged
- **Depends on:** ADR-0001, ADR-0002, ADR-0009, ADR-0013, ADR-0014
- **Supersedes:** Nothing. V4 is a fresh programme and does not alter V1, V2, or V3 evidence.

## Context

ADR-0014 authorizes V4 only as a gate-completeness-first programme. Before V4 has calibration cases, final-evaluation cases, an artifact, or a scheduler, the project must freeze the full experimental method that will govern those later assets.

The purpose is not to make a positive result more likely. The purpose is to make any result inspectable:

- a V4 calibration pass must mean every predeclared gate was actually calculated and retained;
- V4 final outcomes must never select calibration settings, thresholds, fixtures, or policy rules;
- a failed gate must produce a bounded fallback rather than a silent promotion;
- a future policy comparison must use the same immutable V4 final corpus for every valid policy and baseline.

V4 may learn only one process lesson from V3: final-gate completeness must be executable and tested before final evidence exists. V3 case bytes, outcomes, metric values, artifact parameters, and policy choices are not V4 inputs.

## Decision

V4 will use one fixed calibration method, one valid adaptive policy family, three valid baselines, one unsafe retrospective negative control, a fixed replay score, and a complete held-out calibration gate.

No V4 case asset may be written until the V4 final-assessment contract and non-final test harness implement these rules.

## 1. Fresh V4 evidence constitution

V4 uses a new root and new namespace:

```text
fixture root:
data/fixtures/synthetic_calibration_redesign_v4/

case namespace:
CRV4-###
```

The V4 evidence plan is fixed before authoring.

| Split | Cases | Candidate positions per case | Observations | Purpose |
|---|---:|---:|---:|---|
| Calibration | 48 | 4 | 192 | Fit the V4 calibrator only. |
| Final evaluation | 36 | 4 | 144 | One held-out calibration gate and, only after a passing gate, policy comparison. |
| Adversarial regression | 12 | 4 | 48 | Protect named causal, provenance, and policy failures. Never tune on this split. |

The final-evaluation corpus will contain four declared capacity families with nine cases each:

```text
CRV4-FINAL-LIGHT-CAPACITY
CRV4-FINAL-MODERATE-CAPACITY
CRV4-FINAL-SATURATED-CAPACITY
CRV4-FINAL-JAGGED-CAPACITY
```

Each final capacity family must contain exactly three self-authored cases for each workload type:

```text
structured_text
code
open_ended_chat
```

Runtime inputs and expected outcomes must remain separate physical assets. Final outcome files remain unavailable to fitting, tuning, fixture-design, and scheduler code.

## 2. V4 calibration method

V4 uses:

```text
method_id=regularized-isotonic-calibration-v4
```

This is a fresh predeclared method. It must not read V3 calibration artifacts, bins, fitted outputs, final outcomes, or metric values.

### Fixed method settings

| Setting | V4 value |
|---|---:|
| Input feature | Pre-sample `conditional_survival_confidence` only |
| Fit split | V4 calibration only |
| Planned calibration observations | 192 |
| Equal-count groups | 12 |
| Minimum observations per group | 16 |
| Smoothing | Laplace: `(successes + 1) / (count + 2)` |
| Ordering rule | Weighted pooled-adjacent-violators monotonic merge |
| Output lower bound | `0.01` |
| Output upper bound | `0.99` |
| Final-evaluation refit | Forbidden |
| Calibration artifact | Frozen, hash-addressed, and immutable before final evidence authoring |

The fitted mapping must be finite, non-decreasing, deterministic for identical verified calibration inputs, and bounded inside the closed interval `[0.01, 0.99]`.

## 3. Complete V4 held-out calibration gate

The V4 final-assessment contract must retain every input, every metric, every gate boolean, and the final decision in one typed machine-readable result.

### Required aggregate metrics

```text
raw_brier_score
calibrated_brier_score
brier_score_improvement

raw_ece_10_bin
calibrated_ece_10_bin
ece_10_bin_improvement

raw_auroc
calibrated_auroc
auroc_delta
```

AUROC is calculated with a deterministic tie-aware Mann-Whitney formulation:

```text
- sort by probability ascending;
- assign average ranks to tied probabilities;
- compute AUROC from positive-class rank sums;
- reject a corpus with no positive or no negative outcomes;
- retain the calculation version in the final result.
```

### Required per-position evidence

For each candidate position `1` through `4`, retain:

```text
observation_count
raw_brier_score
calibrated_brier_score
brier_score_improvement
raw_ece_10_bin
calibrated_ece_10_bin
ece_10_bin_improvement
raw_auroc
calibrated_auroc
auroc_delta
```

### Fixed pass criteria

A V4 held-out calibration result may report a complete pass only when all conditions below are true.

| Gate ID | Requirement |
|---|---|
| `manifest_integrity_passed` | Every immutable final runtime/outcome asset matches the final manifest hash and byte count. |
| `provenance_alignment_passed` | Final manifest, V4 calibration manifest, registry, frozen artifact, and fit report match their retained identity and hashes. |
| `observation_coverage_passed` | Exactly 36 final cases and 144 final observations are loaded. |
| `per_position_coverage_passed` | Every candidate position has exactly 36 observations. |
| `brier_improvement_passed` | `brier_score_improvement >= 0.010`. |
| `ece_improvement_passed` | `ece_10_bin_improvement >= 0.020`. |
| `ranking_safety_passed` | `calibrated_auroc >= raw_auroc - 0.002`. |
| `no_refit_passed` | No calibration fit, artifact mutation, threshold selection, or mapping replacement occurred during final assessment. |
| `no_policy_execution_passed` | No scheduler, baseline, policy comparison, capacity-policy computation, or runtime action was executed during final calibration assessment. |
| `write_once_precheck_passed` | Existing final-result destination was rejected before final fixtures could be loaded or scored. |
| `canonical_serialization_passed` | Canonical output serialization was proven deterministic on approved non-final constructed inputs. |

The final assessment result must retain all gate booleans. A pass is legal only when every boolean is true.

### Gate statuses

The V4 assessment must emit exactly one status:

```text
PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE
CALIBRATOR_REGRESSION
INSUFFICIENT_HELD_OUT_COVERAGE
RANKING_SAFETY_REGRESSION
INCOMPLETE_GATE_EVIDENCE
INVALID_PROVENANCE
```

Status precedence is fixed:

```text
INVALID_PROVENANCE
→ INCOMPLETE_GATE_EVIDENCE
→ INSUFFICIENT_HELD_OUT_COVERAGE
→ RANKING_SAFETY_REGRESSION
→ CALIBRATOR_REGRESSION
→ PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE
```

`CALIBRATOR_REGRESSION` includes failure of either fixed Brier or ECE improvement floor.

Every non-pass status must produce:

```text
adaptive_policy_research_eligibility=blocked
runtime_control_eligible=false
fallback=CONSERVATIVE_FALLBACK
fallback_policy_id=fixed_short_1
reason=complete_v4_calibration_gate_not_passed
```

A complete pass permits only controlled replay-policy research. It does not authorize runtime control, live serving, production claims, or a policy-advantage claim.

## 4. Valid adaptive policy family

V4's valid adaptive policy is:

```text
policy_id=causal-calibrated-prefix-utility-v4
```

For position `k`, the policy may use only:

- request ID, trace ID, declared workload metadata, and candidate position;
- lawfully visible earlier prefix state and earlier calibrated confidences;
- current position pre-sample raw confidence;
- current position calibrated confidence from the frozen V4 artifact;
- current declared capacity profile and fixed marginal capacity cost;
- this ADR's fixed policy configuration;
- the complete V4 calibration-gate result.

It must not use:

- current or future candidate-token values not lawfully visible;
- observed acceptance outcomes;
- prefix-survival labels;
- future capacity state;
- retrospective best-prefix knowledge;
- final-evaluation outcomes;
- any oracle or unsafe-control signal.

The policy uses:

```text
prefix_survival_probability(k)
  = product(calibrated_confidence(1..k))

admit position k only when:
  calibrated_confidence(k) >= 0.60
  and prefix_survival_probability(k) - marginal_capacity_cost(k) >= 0.08
```

The maximum verification length is four positions.

A causal guard must reject forbidden information access with:

```text
forbidden_future_information_access
```

## 5. Valid baselines and invalid negative control

All V4 policy comparisons must include the following valid baselines.

| Policy ID | Fixed behavior |
|---|---|
| `fixed_short_1` | Admit the first candidate position only. |
| `fixed_long_4` | Admit up to four positions, regardless of confidence or capacity. |
| `static_raw_threshold_0_72` | Admit sequential positions while raw confidence is at least `0.72`, up to four positions. |

The unsafe retrospective control is evaluation-only:

```text
policy_id=unsafe_retrospective_oracle_v4
classification=test_only_invalid_control
```

It may use forbidden outcome knowledge only to prove that the causal guard and report labelling reject it. Its output must always be labelled:

```text
INVALID_CAUSAL_COMPARISON
```

It must never appear in a valid baseline leaderboard or recommendation.

## 6. Fixed replay score and comparison result labels

Each policy receives the same frozen case order, runtime inputs, declared capacity profile, and scoring function.

For one replay case:

```text
accepted_work
  = admitted positions that survive until the first observed rejection

verification_waste
  = admitted_positions - accepted_work

capacity_cost
  = sum(declared marginal capacity costs for admitted positions)

realized_policy_utility
  = accepted_work - 0.25 * verification_waste - capacity_cost
```

This is a controlled synthetic replay score. It is not throughput, cost, latency, live-traffic, or production evidence.

A final policy-comparison report may use only:

| Result label | Meaning |
|---|---|
| `VALID_ADAPTIVE_ADVANTAGE` | The adaptive policy is causally valid and beats both `fixed_long_4` and `static_raw_threshold_0_72` by at least `0.10` mean utility in both saturated and jagged capacity profiles, with no capacity family below `-0.05` mean utility versus either named baseline. |
| `VALID_CONDITIONAL_ADVANTAGE` | The adaptive policy is causally valid and beats both named baselines by at least `0.10` mean utility in at least one complete named capacity profile, without satisfying the stronger advantage condition. |
| `VALID_NEUTRAL_OR_MIXED_RESULT` | The comparison is causally valid and complete but no advantage condition is satisfied. |
| `CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY` | The complete V4 calibration gate did not pass; conservative fallback is reported instead. |
| `INVALID_CAUSAL_COMPARISON` | A policy accessed forbidden future information or violated the causal contract. |
| `INVALID_PROVENANCE` | Inputs, manifests, hashes, configurations, or evidence roles were not aligned. |

## 7. Required V4 assessment contract and tests before fixture authoring

Before any V4 fixture byte is authored, the repository must contain:

```text
src/specsafe/heldout_calibration/v4_final_assessment.py
tests/test_v4_final_assessment_contract.py
```

The exact implementation may use different package internals, but it must expose strict Pydantic contracts for:

```text
V4FinalAssessmentProtocol
V4FinalAssessmentGateChecks
V4FinalProbabilityMetrics
V4FinalPositionMetrics
V4FinalHeldOutAssessmentResult
```

The non-final test harness must prove all of the following without loading V4 final evidence:

- missing AUROC or incomplete metric fields are rejected;
- Brier/ECE improvements that pass while ranking safety fails yield `RANKING_SAFETY_REGRESSION`;
- insufficient aggregate or position coverage yields `INSUFFICIENT_HELD_OUT_COVERAGE`;
- missing or false gate evidence cannot yield a complete pass;
- final provenance mismatches yield `INVALID_PROVENANCE`;
- calibration refit or policy execution flags cannot coexist with a pass;
- runtime-control eligibility cannot be true;
- write-once result destinations are rejected before assessment loading;
- canonical JSON is byte-identical for equivalent approved non-final constructed result objects;
- the unsafe retrospective control is rejected and labelled invalid.

The V4 final-assessment runner must be write-once and must:

1. reject a pre-existing result destination before loading final fixtures;
2. verify the final manifest and all relevant provenance hashes;
3. load a frozen artifact only;
4. score raw and calibrated final observations once;
5. write canonical JSON with all required metrics and gate checks;
6. never invoke a scheduler or policy during calibration assessment.

## 8. Evidence controls and prohibited work

Until the V4 assessment contract and its non-final test harness are merged, V4 must not:

```text
- author V4 runtime or outcome case assets;
- create V4 final manifests;
- fit a V4 calibrator;
- write V4 scheduler, baseline, capacity, or replay-evaluation code;
- use V3 evidence values to tune V4 settings;
- run Kaggle, UI, serving, or public-demo work;
- make a V4 calibration or policy-performance claim.
```

## Acceptance criteria for the next slice

The next V4 implementation slice is authorized only after this ADR is merged.

It must implement the V4 final-assessment contract and non-final test harness. It must not author, load, score, or disclose V4 final evidence.

## Claims after this ADR

### Permitted

- SpecSafe has frozen a V4 method, full calibration gate, valid policy family, baselines, score, fallback, and evidence roles before V4 data authoring.
- The V4 programme has a predeclared path to a complete, auditable held-out calibration decision.

### Forbidden

- V4 calibration or final-evaluation evidence exists.
- A V4 calibrator has been fit.
- A V4 policy or scheduler has been implemented or evaluated.
- The V4 adaptive policy improves utility.
- Any runtime-control, live-serving, throughput, cost, or production claim.

## Final control statement

> V4's success condition is fixed before V4 data exists: complete calibration evidence first, causal policy evidence second, and no promotion without every required gate field.
