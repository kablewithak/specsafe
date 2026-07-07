# V5 Controlled Synthetic Policy Comparison

## Validity marker

```text
VALID_COMPARISON
```

## Objective

Evaluate fixed-length, static-threshold, and calibrated causal load-aware verification policies on one immutable synthetic corpus using identical trace inputs, declared synthetic capacity profiles, and one shared utility scorer.

## Evidence class and maturity

```text
evidence_class=synthetic_controlled
evidence_maturity_label=synthetic_fixture_validated
phase5_gate_status=passes_controlled_synthetic_phase5_gate
```

This is controlled synthetic replay evidence. It is not final held-out policy evaluation, Kaggle measurement, live-serving evidence, or production evidence.

## Governed inputs

| Input | Relative path | SHA-256 |
|---|---|---|
| Matched comparison result | `evidence/matched-policy-comparison/v5-controlled-synthetic-comparison-v1/result.json` | `e82e21853526e687b068cd8a0b3abb4bb390da755be977bf5f3045148a7d17f4` |
| Matched comparison fixture manifest | `data/fixtures/synthetic_matched_policy_comparison_v1/manifest.json` | `d4ea55d7e4fee04b60af949f1cd26189c48233eac5770ec852c5b69066b8d31c` |
| Synthetic capacity-profile manifest | `data/fixtures/synthetic_capacity_profiles/v1/manifest.json` | `3a7c56e56804c82ce87173a291cef0a1577a788ff461b9f56bc2e51d725dfe0d` |
| Retained V5 calibration artifact | `data/fixtures/synthetic_calibration_successor_v5/bounded_monotone_beta_calibration_artifact.json` | `a3baeb2db94221d68a69fc757c8865e384e3ac92ca05585919188fe1c744cd14` |
| Retained V5 calibration eligibility assessment | `evidence/heldout-calibration/v5-final-heldout-calibration-assessment-v1/result.json` | `f985ef8df30a5d920194a05f7d5115431420f8ed40a1252d33af62f5d0882ab9` |

## Predeclared policy and scoring configuration

```text
comparison_id=v5-controlled-synthetic-comparison-v1
fixed_length_policy_id=fixed-matched-corpus-v1
static_threshold_policy_id=threshold-matched-corpus-v1
adaptive_policy_id=adaptive-matched-corpus-v1
unsafe_policy_id=unsafe-retrospective-lookahead-v1
fixed_length=4
static_threshold=0.6
policy_utility=accepted_admission_count × 1.0 − Σ(admitted marginal verification cost × 1.0)
protocol_configuration_sha256=6a700e2aba18cde5ba06569506eb7cc3d70334bacd46047b4748e5b120070bbf
```

## Aggregate case-level outcomes

| Comparator | Adaptive higher utility | Neutral | Adaptive lower utility |
|---|---:|---:|---:|
| Fixed-length | 2 | 3 | 1 |
| Static threshold | 3 | 2 | 1 |

The retained corpus includes higher, neutral, and lower adaptive-policy outcomes. This mixed result is required evidence, not a defect to hide.

## Case-level results

| Case | Split | Capacity profile | Fixed utility | Threshold utility | Adaptive utility | Adaptive vs fixed | Adaptive vs threshold |
|---|---|---|---:|---:|---:|---|---|
| MPC5-101 | development | flat_capacity_control | 3.6 | 3.6 | 3.6 | utility_neutral | utility_neutral |
| MPC5-102 | development | light_load | 3.6 | 3.6 | 3.6 | utility_neutral | utility_neutral |
| MPC5-103 | development | moderate_load | 1 | 1 | 0 | adaptive_lower_utility | adaptive_lower_utility |
| MPC5-104 | development | saturated_load | -13 | -13 | 0 | adaptive_higher_utility | adaptive_higher_utility |
| MPC5-105 | development | jagged_capacity | -7.8 | -7.8 | 0 | adaptive_higher_utility | adaptive_higher_utility |
| MPC5-106 | adversarial_regression | flat_capacity_control | 1.6 | 0 | 1.6 | utility_neutral | adaptive_higher_utility |

## Causal safety and unsafe control

- Valid matched comparisons retained: `6`.
- Unsafe retrospective controls excluded: `6`.
- Every unsafe control is `causal_safety_status=fail` and remains excluded from valid scores and adaptive-versus-baseline deltas.

## Phase 5 gate decision

```text
phase5_gate_status=passes_controlled_synthetic_phase5_gate
kaggle_experiment_authorized=true
public_replay_release_authorized=false
runtime_control_eligible=false
promotion_eligible=false
```

The local controlled-synthetic proof is complete enough to begin the separately labelled Kaggle evidence-acquisition phase. This authorization does not elevate the maturity label or permit public replay, runtime control, or production claims.

## Supported claims

- Under this six-case controlled synthetic corpus, the calibrated causal policy had mixed case-level utility relative to both valid baselines.
- The retained corpus preserves adaptive-policy higher, neutral, and lower utility cases.
- Unsafe retrospective control results failed causal safety and were excluded.
- The local core evidence is sufficient to start a separately labelled Kaggle experiment.

## Non-claims

- No global policy winner is established.
- No final held-out policy comparison has been performed.
- No production throughput, latency, cost-saving, or serving-capacity result is established.
- No runtime-control, promotion, public replay release, or production-readiness claim is established.

## Reproduction

```powershell
python -m specsafe.reporting.controlled_synthetic_comparison --project-root . --check
```
