# SpecSafe V3 Method and Evidence Constitution

## Status

**Accepted design record.**

This is the final decision record made before V3 data exists. It says what we will test, how we will test it, and what we will call a win, a mixed result, or a safe stop.

## Plain-English goal

We want to test whether an AI can decide when another check is worth the effort better than three simple rules:

1. always check only one step;
2. always check up to four steps;
3. keep checking while a raw confidence score stays above one fixed line.

The smarter V3 policy is allowed to consider confidence and current system pressure. It is not allowed to see the answer before making its decision.

## Frozen V3 question

> Under fixed V3 replay conditions, does `causal-marginal-prefix-v1` use checking effort more usefully than `fixed_long_4` and `static_raw_threshold_0_70`, while using only lawful decision-time information and safely falling back when confidence is not trustworthy enough?

## What is fixed before V3 evidence exists

| Area | V3 decision |
|---|---|
| Calibration method | `quantile-isotonic-calibration-v1` |
| Calibration input | Raw confidence only |
| Calibration fit data | V3 calibration split only |
| Valid adaptive policy | `causal-marginal-prefix-v1` |
| Maximum candidates | 4 |
| Minimum calibrated confidence | `0.55` |
| Minimum expected value after capacity cost | `0.05` |
| Conservative fallback | `fixed_short_1` |
| Fixed baselines | `fixed_short_1`, `fixed_long_4`, `static_raw_threshold_0_70` |
| Report score | Accepted work minus declared capacity cost |
| Final assessment attempts | One locked assessment and one locked comparison run |

## Why this is a fair test

The confidence cleaner is selected now, before V3 calibration and final data are written. The policy settings are also selected now.

Later, we can say one of two honest things:

- “This predeclared policy helped in these named conditions.”
- “This predeclared policy did not help enough, or safely fell back.”

We may not quietly change the confidence cleaner, score, threshold, capacity rules, or final cases after seeing the result.

## The V3 confidence cleaner

### Name

`quantile-isotonic-calibration-v1`

### What it does

It sorts V3 calibration confidence scores from low to high and divides them into eight equally sized groups. For every group, it calculates how often the prediction was actually right. It then makes sure the learned confidence values still move from low to high.

This is useful because raw confidence may be wrong in a curved or uneven way. The method is flexible enough to learn a simple curve but constrained enough to remain easy to inspect.

### Fixed fitting rules

```text
calibration observations: 144 planned
confidence groups: 8
minimum observations in every group: 12
smoothing: add 1 success and 1 failure before calculating the group rate
ordering: merge neighbouring groups only when their success rates would otherwise go backwards
allowed output range: 0.02 to 0.98
```

### What it may read

```text
V3 calibration raw confidence
V3 calibration observed acceptance label
```

### What it may never read

```text
V3 final-evaluation files
V3 final scores
V1 or V2 final-evaluation assets
V1 or V2 calibration artifact values
future candidate tokens
future verification outcomes during runtime policy decisions
```

## The V3 smart policy

### Name

`causal-marginal-prefix-v1`

### Decision idea

At each candidate position, the policy asks:

> “Based only on what I know right now, is the likely value of checking this next position bigger than the current cost of checking it?”

It starts with the calibrated confidence for the current position. It multiplies that by the calibrated confidences of earlier positions to estimate the chance that the full prefix through this point will survive.

It admits the next position only when:

```text
calibrated confidence is at least 0.55
and
estimated prefix value minus current capacity cost is at least 0.05
```

It stops at four positions even if the conditions continue to hold.

### Safe fallback

If the hidden-test calibration gate does not pass, the policy does not pretend it has useful probabilities.

Instead it uses:

```text
CONSERVATIVE_FALLBACK
fixed_short_1
```

That means it checks one position only and makes no probability-driven length decision.

## The rules it must beat

| Policy | Plain-English behaviour |
|---|---|
| `fixed_short_1` | Always check one position. |
| `fixed_long_4` | Always check up to four positions. |
| `static_raw_threshold_0_70` | Keep checking while raw confidence remains at least 0.70. |

These rules are deliberately simple. They make it possible to see whether complexity earns its place.

## V3 evidence plan

### Calibration corpus

```text
36 fresh self-authored cases
4 candidate positions per case
144 observations
```

Purpose: learn the calibration map only.

### Final-evaluation corpus

```text
24 fresh self-authored cases
4 candidate positions per case
96 observations
four capacity families
three workload types in every family
```

Purpose: one final calibration assessment and one policy comparison.

### Adversarial regression corpus

```text
8 fresh self-authored cases
4 candidate positions per case
32 observations
```

Purpose: keep known dangerous failures visible. It is not a tuning set.

## Required V3 final families

| Family | Cases | What it tests |
|---|---:|---|
| `V3-FINAL-LIGHT-CAPACITY` | 6 | When extra checking is cheap and fixed-long may be competitive. |
| `V3-FINAL-MODERATE-CAPACITY` | 6 | When choices begin to matter but no single rule should dominate automatically. |
| `V3-FINAL-SATURATED-CAPACITY` | 6 | When expensive extra checking should be used carefully. |
| `V3-FINAL-JAGGED-CAPACITY` | 6 | When system pressure changes unevenly and simple greedy choices can become brittle. |

Every family includes:

```text
2 structured_text cases
2 code cases
2 open_ended_chat cases
```

## How we score the policies

After each policy has decided what to check, the scorer may look at the stored outcomes.

```text
accepted work = admitted positions that survive before the first rejection
verification waste = admitted positions - accepted work
capacity cost = sum of the costs of admitted positions
utility = accepted work - capacity cost
```

This is a replay score for controlled tests. It is not a claim about production speed or money saved.

## Calibration pass gate

Before the smart probability-driven policy can run as valid, all of these must be true on the locked V3 final set:

```text
at least 96 observations
all final files match the locked manifest
calibrated Brier score improves by at least 0.005
calibrated 10-bin ECE improves by at least 0.010
calibrated AUROC does not fall by more than 0.001
at least 20 observations exist at each candidate position
rebuild is byte-for-byte identical
```

A failure means fallback, not retuning.

## Predeclared final outcomes

| Outcome | Meaning |
|---|---|
| `VALID_ADAPTIVE_ADVANTAGE` | The smart policy clears every gate and beats both main baselines by at least 0.10 mean utility in saturated and jagged capacity. |
| `VALID_CONDITIONAL_ADVANTAGE` | The smart policy clears every gate and beats both main baselines by at least 0.10 mean utility in at least one complete named capacity family. |
| `VALID_NEUTRAL_OR_MIXED_RESULT` | The test is valid, but no predeclared advantage threshold is met. |
| `CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY` | Confidence is not trustworthy enough, so fallback is used. |
| `INVALID_CAUSAL_COMPARISON` | A policy cheated by using forbidden information; its score is invalid. |

## Non-negotiable data rule

V3 uses a new directory, new IDs, new self-authored tasks, new confidence values, new labels, and new final manifests.

V1 and V2 final-evaluation material cannot be used to shape V3 data, policy settings, or result interpretation.

## Next authorised engineering step

Build the V3 evidence schema and registry boundary. Do not author calibration or final cases yet.
