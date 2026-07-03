# ADR-0010: Freeze the V3 Method and Evidence Constitution Before V3 Data Exists

- **Status:** Accepted
- **Date:** 2026-07-03
- **Decision owner:** Kabo Molefe
- **Applies from:** `main` after PR #41 (`b6fa2ee`)
- **Depends on:** ADR-0009 and the V3 full north-star programme charter

## Context

V3 is authorised to pursue SpecSafe's full north star: determine, under fair replay conditions, whether a valid verification policy can spend limited checking effort more intelligently than simple fixed rules.

This decision must happen before V3 case files, manifests, calibration fitting code, or scheduler code exist. Otherwise the project could quietly pick a method after seeing which one performs best.

V1 and V2 remain closed historical experiments. Their final-evaluation assets, fit values, and result details must not influence this V3 choice.

## Decision

V3 will use one fixed calibration method, one fixed valid policy family, fixed baselines, a fixed score, and a fixed fallback rule.

### 1. Calibration method

V3 will use **`quantile-isotonic-calibration-v1`**.

Plain English: it groups similar confidence scores into eight evenly sized groups, learns the observed success rate in each group from V3 calibration data, and forces the groups to remain in sensible low-to-high order.

The method is fixed as follows:

| Setting | Fixed V3 value |
|---|---:|
| Input feature | `raw_confidence` only |
| Fit split | V3 calibration split only |
| Calibration observations | 144 minimum, 144 planned |
| Number of groups | 8 equal-count groups |
| Minimum observations per group | 12 |
| Smoothing | Laplace: `(successes + 1) / (count + 2)` |
| Ordering rule | Weighted pooled-adjacent-violators monotonic merge |
| Output lower bound | `0.02` |
| Output upper bound | `0.98` |
| Final-evaluation refit | Forbidden |

The output is a non-decreasing confidence map. It may produce ties, but it may not reverse the confidence order.

### 2. Valid policy family

V3 will use **`causal-marginal-prefix-v1`**.

For each candidate position, the policy may use only:

- request and workload metadata;
- current candidate position;
- lawfully visible earlier prefix state;
- the current position's pre-sample raw confidence;
- the calibrated confidence produced by the frozen V3 map;
- earlier calibrated confidences already available in the same decision path;
- the declared current capacity profile and its marginal cost;
- fixed policy settings and the global calibration-fitness result.

It must not use candidate-token values that are not yet lawfully visible, observed labels, future verification results, retrospective best prefixes, or any final-evaluation outcome.

The policy estimates the chance that the full admitted prefix through position `k` survives as the product of calibrated confidences available through `k`. It admits the next position only when both conditions hold:

```text
calibrated_confidence >= 0.55
expected_prefix_value - marginal_capacity_cost >= 0.05
```

Where:

```text
expected_prefix_value = product of calibrated confidences for positions 1..k
```

The maximum V3 verification length is four candidate positions.

### 3. Conservative fallback

A probability-driven V3 policy is permitted only after the locked V3 held-out calibration assessment passes.

If it does not pass, the adaptive policy must return:

```text
CONSERVATIVE_FALLBACK
fallback_policy_id=fixed_short_1
reason=confidence_not_fit_for_automated_scheduling
```

`fixed_short_1` admits only the first candidate position and does not use probability values to make a length decision.

### 4. Fixed baselines

All V3 reports must include these valid baselines:

| Policy ID | Fixed behaviour |
|---|---|
| `fixed_short_1` | Admit the first position only. |
| `fixed_long_4` | Admit up to four positions, regardless of confidence or capacity. |
| `static_raw_threshold_0_70` | Admit sequential positions while raw confidence is at least `0.70`, up to four positions. |

The unsafe retrospective control remains evaluation-only and must be labelled invalid in every report.

### 5. Calibration fitness gate

The V3 final-evaluation calibration assessment passes only when all of the following are true:

| Gate | Requirement |
|---|---|
| Manifest integrity | Every locked V3 final file matches its manifest hash and byte count. |
| Sample count | At least 96 final observations. |
| Brier quality | Calibrated Brier score improves over raw by at least `0.005`. |
| Calibration error | Calibrated 10-bin ECE improves over raw by at least `0.010`. |
| Ranking safety | Calibrated AUROC is no more than `0.001` below raw AUROC. |
| Position coverage | Each of positions 1 to 4 has at least 20 final observations. |
| Determinism | Rebuilding the assessment produces byte-identical output. |

A failed gate is not a broken test. It is a valid result that forces conservative fallback and blocks a probability-driven adaptive-policy claim.

### 6. Policy-comparison score

Each admitted candidate position is scored after decisions are recorded.

```text
accepted_work = admitted positions that survive until the first observed rejection
verification_waste = admitted_positions - accepted_work
capacity_cost = sum of declared marginal costs for admitted positions
realized_policy_utility = accepted_work - capacity_cost
```

This is a controlled replay score, not production throughput or cost evidence.

### 7. Result labels

After the locked final comparison, the report may use only these result labels:

| Result label | Predeclared meaning |
|---|---|
| `VALID_ADAPTIVE_ADVANTAGE` | The adaptive policy passes every gate and beats both `fixed_long_4` and `static_raw_threshold_0_70` by at least `0.10` mean utility in both saturated and jagged profiles. |
| `VALID_CONDITIONAL_ADVANTAGE` | The adaptive policy passes every gate and beats both named baselines by at least `0.10` mean utility in at least one complete named capacity profile. |
| `VALID_NEUTRAL_OR_MIXED_RESULT` | The comparison is valid but the advantage requirements are not met. |
| `CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY` | The calibration gate fails and fallback is used. |
| `INVALID_CAUSAL_COMPARISON` | A policy accessed forbidden information; its apparent utility is invalid. |

## Fresh V3 evidence constitution

V3 will use a separate root:

```text
data/fixtures/synthetic_verification_policy_v3/
```

Planned evidence sizes are fixed before authoring:

| Split | Case count | Candidate positions per case | Observation count | Purpose |
|---|---:|---:|---:|---|
| Calibration | 36 | 4 | 144 | Fit the frozen calibrator only. |
| Final evaluation | 24 | 4 | 96 | One locked calibration assessment and policy comparison. |
| Adversarial regression | 8 | 4 | 32 | Protect named known failures; never tune on it. |

V3 final cases are organised into four six-case capacity families:

- `V3-FINAL-LIGHT-CAPACITY`
- `V3-FINAL-MODERATE-CAPACITY`
- `V3-FINAL-SATURATED-CAPACITY`
- `V3-FINAL-JAGGED-CAPACITY`

Each final family must include two self-authored cases for each workload type:

- `structured_text`
- `code`
- `open_ended_chat`

## Consequences

### Positive

- The project now has a clear, inspectable V3 hypothesis before data exists.
- A future positive result cannot be created by changing the method after seeing final outcomes.
- V3 can report a conditional advantage without hiding cases where simple rules win.

### Costs and risks

- The fixed gate may fail, which blocks the intended adaptive claim.
- The fixed policy may be neutral or worse than a baseline.
- A new V4 experiment, not an in-place edit, would be required for a material method change after final V3 evidence is authored.

## Status after merge

This ADR authorizes V3 evidence authoring under the fixed method and corpus constitution. It does not authorize final-evaluation authoring until the V3 calibration corpus, fitter, and local calibration-readiness gate are merged and reproducible.
