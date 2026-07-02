# Calibration Redesign Protocol

- **Protocol ID:** `calibration-redesign-protocol-v1`
- **Status:** Pre-fit governance document
- **Evidence class:** Synthetic controlled evidence
- **Related ADR:** `ADR-0003-calibration-redesign-boundary.md`
- **Current phase:** Phase 3 remediation / calibration redesign boundary
- **Current authorization:** Documentation and fresh-fixture design only
- **Current prohibition:** Do not fit, tune, or evaluate a redesigned calibrator yet

## 1. Purpose

This protocol governs a new calibration attempt after the prior frozen equal-width
histogram calibrator regressed on its held-out assessment.

It exists to make the next experiment inspectable before outcomes exist. It prevents
the consumed `STF-004` final-evaluation fixture from becoming a hidden optimization
target and prevents an adaptive scheduling policy from being built on unpromoted
confidence.

The protocol answers one narrower question:

> With fresh, separated synthetic evidence, does a predeclared one-parameter logit
> temperature transformation improve the probability reliability of raw conditional
> survival confidence without violating split or provenance controls?

This protocol does not evaluate a scheduler. It does not define policy utility. It does
not create a production-serving claim.

## 2. Inherited facts and hard boundaries

### 2.1 Retained prior result

```text
prior_method=equal-width histogram calibrator
prior_fit_split=STF-005 and STF-006 calibration fixtures
prior_final_evaluation=STF-004
prior_result=calibrator_regression
prior_promotion=not promoted
```

### 2.2 Quarantine rule

```text
STF-004 status=consumed held-out evidence
STF-004 allowed use=record the prior non-promotion outcome
STF-004 forbidden use=all redesign, fitting, tuning, fixture selection, threshold
selection, method selection, or comparative validation
```

`STF-005` and `STF-006` are also excluded from the new calibration and final-evaluation
assets. Their role was limited to the prior artifact’s calibration protocol.

### 2.3 Causal boundary

Calibration is still post-hoc evaluation work. Observed acceptance outcomes must remain
outside valid runtime policy input. No work in this protocol may widen
`CausalSchedulerContext`, weaken the causal guard, or add policy access to labels.

## 3. Candidate artifact

### 3.1 Identity

```text
artifact_id=logit-temperature-scaling-v1
artifact_version=1
method=single-positive-temperature-on-logit-confidence
scope=global
input=conditional_survival_confidence
output=calibrated_conditional_survival_confidence
```

### 3.2 Conceptual transformation

For a valid confidence value `p` strictly between zero and one:

```text
calibrated(p) = sigmoid(logit(p) / temperature)
```

The fitted `temperature` is strictly positive and global. Confidence values at the
contract boundary must follow a documented clipping policy before a logit is calculated.

### 3.3 Intentionally excluded complexity

This protocol does not permit:

- per-workload temperatures;
- per-position temperatures;
- learned bin edges;
- isotonic regression;
- multi-parameter calibration;
- ensembling;
- result-dependent fallback selection;
- post-hoc selection among multiple calibration methods;
- final-evaluation-driven hyperparameter search.

The narrowness is deliberate. The next candidate must earn promotion with minimal
flexibility.

## 4. Evidence design

### 4.1 New fixture-set identity

The future fixture proposal must use a new identity, for example:

```text
fixture_set_id=synthetic-calibration-redesign-v1
fixture_set_version=1.0.0
source_type=synthetic
```

The exact final name may differ only if it is decided before fixture generation and
recorded consistently across the manifest, tests, artifact, and report.

### 4.2 Required split structure

| Split | Purpose | Minimum observations |
|---|---|---:|
| `development_diagnostic` | Validate fixtures and protocol plumbing. | 24 |
| `calibration` | Fit the single temperature only. | 60 |
| `fresh_final_evaluation` | Assess frozen raw-versus-calibrated fitness. | 30 |
| `adversarial_regression` | Preserve named leakage and failure controls. | Case-defined |

Allowed influence is fixed by split role:

- `development_diagnostic`: schema, loader, and deterministic implementation debugging only;
- `calibration`: the temperature parameter only;
- `fresh_final_evaluation`: nothing before final report generation;
- `adversarial_regression`: regression protection only.

Observation counts are minimum gates, not a claim of statistical sufficiency for broad
generalization.

### 4.3 Scenario-family isolation

Every fixture case must include a `scenario_family_id`. The fixture generator and
manifest validation must reject a split assignment where the same scenario family appears
in both `calibration` and `fresh_final_evaluation`.

A scenario family represents a shared underlying pattern, not merely a case identifier.
Examples may include:

- monotonic overconfidence;
- monotonic underconfidence;
- early confidence decay;
- late suffix collapse;
- high-confidence stable prefix;
- workload-specific confidence distribution.

The exact scenario catalogue must be frozen before outcome labels are authored for the
fresh final-evaluation set.

### 4.4 Coverage requirements

The new calibration and fresh final-evaluation splits must each include:

- all project workload classes represented in the fixture contract;
- multiple candidate-position ranges;
- both overconfidence and underconfidence patterns;
- at least one neutral pattern where raw confidence is already reasonable;
- enough confidence spread to exercise the full declared clipping interval;
- explicit provenance and source-type fields.

The data are still synthetic. Reports must not generalize from these fixtures to
production traffic, a model family, a serving engine, or a customer workload.

## 5. Freeze-before-fit protocol

The following must be committed before fitting begins:

```text
- fixture-set manifest and hashes
- split assignments
- scenario-family registry
- temperature optimization objective
- optimizer implementation and deterministic seed policy, if applicable
- confidence clipping epsilon
- allowed temperature range
- minimum calibration observation count
- fixed ECE bin-count and bin edges
- raw and calibrated metric definitions
- report schema and required provenance fields
- promotion criteria
- typed non-promotion states
- no-fit and conservative-fallback behavior
```

Any change to these items after fresh final-evaluation outcomes are inspected invalidates
the evaluation for promotion purposes and requires a new fixture set and fresh final
evaluation boundary.

## 6. Fit protocol

### 6.1 Eligibility

Fit only when all conditions hold:

```text
calibration_split_present=true
calibration_observation_count>=60
manifest_hash_valid=true
scenario_family_isolation_valid=true
input_confidences_contract_valid=true
```

### 6.2 Objective

Fit the temperature on the calibration split using the predeclared binary
negative-log-likelihood objective. The implementation must retain:

- source fixture-set ID and version;
- calibration case IDs;
- calibration trace IDs;
- observation count;
- clipping configuration;
- optimizer identity and configuration;
- fitted temperature;
- artifact schema version;
- artifact hash;
- run ID.

### 6.3 No-fit behavior

When eligibility fails or optimization cannot produce a valid positive temperature:

```text
artifact_status=not_fitted
promotion_decision=not_promoted
reason=insufficient_calibration_evidence or calibration_fit_failed
runtime_confidence_state=confidence_not_fit_for_automated_scheduling
```

No silent raw-confidence fallback may be relabelled as a calibrated artifact.

## 7. Held-out assessment protocol

### 7.1 Input boundary

The evaluator may receive:

- the frozen temperature artifact;
- the new `fresh_final_evaluation` fixtures;
- raw confidence values;
- observed outcomes for scoring only;
- fixed metric configuration;
- manifest and provenance metadata.

The evaluator must reject:

- an unfrozen or mutable artifact;
- a fixture from another split;
- an artifact/fixture-set mismatch;
- missing split metadata;
- missing provenance;
- evidence that final outcomes were exposed to the fit path.

### 7.2 Metrics

The report must retain, at minimum:

```text
raw_brier_score
calibrated_brier_score
raw_ece
calibrated_ece
fixed_bin_evidence
observation_count
confidence_ordering_status
manifest_and_artifact_provenance
```

Ranking is not a separate optimization target because a strictly positive global
temperature transformation is monotonic in the input confidence and should preserve
ordering. The report must still validate and record that ordering was preserved.

### 7.3 Promotion gate

The artifact is eligible only for the narrow status
`promotable_for_adaptive_policy_research` when all conditions are true:

```text
fresh_final_evaluation_observation_count >= 30
calibrated_brier_score < raw_brier_score
calibrated_ece < raw_ece
confidence_ordering_status = preserved
manifest_and_artifact_provenance = valid
split_leakage_status = pass
report_provenance_status = complete
```

Any tie is non-promotion. Any missing field is non-promotion. Any causal or split
violation is non-promotion.

### 7.4 Non-promotion statuses

At minimum, use one of:

```text
not_promoted_insufficient_final_evidence
not_promoted_calibrator_regression
not_promoted_no_strict_improvement
not_promoted_split_leakage
not_promoted_artifact_fixture_mismatch
not_promoted_report_provenance_missing
not_promoted_calibration_fit_failed
```

The report must make non-promotion visible rather than presenting only aggregate metrics.

## 8. Trace and report fields

### 8.1 Required artifact provenance

```text
artifact_id
artifact_version
method
temperature
confidence_clipping_epsilon
optimizer_id
optimizer_configuration_hash
fit_fixture_set_id
fit_fixture_set_version
fit_manifest_hash
fit_case_ids
fit_trace_ids
fit_observation_count
artifact_schema_version
artifact_hash
run_id
```

### 8.2 Required held-out report provenance

```text
protocol_id
report_id
run_id
artifact_hash
fresh_final_fixture_set_id
fresh_final_fixture_set_version
fresh_final_manifest_hash
fresh_final_case_ids
fresh_final_trace_ids
fresh_final_observation_count
metric_configuration_hash
raw_brier_score
calibrated_brier_score
raw_ece
calibrated_ece
confidence_ordering_status
split_leakage_status
promotion_decision
non_promotion_reason
generated_at
```

## 9. Failure taxonomy and regression cases

The implementation phase must include deterministic tests for:

1. final-evaluation outcomes cannot reach the fit function;
2. fixture-set ID/version mismatches are rejected;
3. overlap of scenario families across calibration and final evaluation is rejected;
4. missing manifests or hashes are rejected;
5. a non-positive or non-finite temperature is rejected;
6. an insufficient calibration split yields explicit no-fit behavior;
7. a final-evaluation tie on either required metric yields non-promotion;
8. changing a final-evaluation outcome changes only assessment, never the frozen fit;
9. report serialization retains both metrics and the promotion/non-promotion state;
10. runtime policy interfaces remain unchanged and cannot consume post-hoc outcomes.

## 10. Explicit non-goals

This protocol does not:

- implement a causal load-aware policy;
- introduce capacity profiles;
- define policy utility;
- compare policies;
- collect Kaggle evidence;
- create a public demo;
- change the causal runtime contract;
- claim that temperature scaling will succeed;
- claim production throughput, latency, cost savings, losslessness, or readiness.

## 11. Required next safe implementation order

1. Review and merge this governance boundary.
2. Author a fresh fixture-design proposal with scenario-family isolation.
3. Review fixture manifest, split counts, and outcome separation before fixture creation.
4. Implement typed artifact and evaluator contracts.
5. Implement fitting and assessment with deterministic tests.
6. Run the fresh held-out assessment once.
7. Retain the result.
8. Start adaptive-policy work only if the narrow promotion gate passes.

## 12. Acceptance criteria for this documentation slice

This protocol is accepted only when it clearly establishes:

- a candidate method before outcomes;
- permanent quarantine of `STF-004`;
- fresh evidence requirements;
- scenario-family split isolation;
- frozen fitting and metric configuration;
- narrow, strict promotion criteria;
- explicit non-promotion states;
- no policy or production claim path from documentation alone.
