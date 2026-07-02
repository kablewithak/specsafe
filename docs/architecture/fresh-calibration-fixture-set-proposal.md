# Fresh Calibration Fixture-Set Proposal

## Status

```text
proposal_status=governed_design
implementation_status=not_started
fixture_set_id=synthetic-calibration-redesign-v1
fixture_set_version=1.0.0
source_type=synthetic
candidate_calibrator=logit-temperature-scaling-v1
adaptive_policy_status=blocked_pending_fresh_promotion_gate
```

## Purpose

Define the fresh synthetic evidence boundary required to evaluate the predeclared
calibration redesign without contaminating it with the consumed `STF-004` held-out
fixture or with final-evaluation outcomes.

This document is a fixture-authoring protocol. It is not a fixture manifest, a source
code change, a calibration result, or a policy recommendation.

## Governing constraints

1. `STF-004` is historical evidence only and is permanently excluded from redesign.
2. Calibration and final-evaluation assets must be separated by scenario family, not
   only by file name or case identifier.
3. Runtime inputs and expected outcomes must remain separate files and separate
   directories.
4. The new method remains `logit-temperature-scaling-v1` until a future governed ADR
   explicitly changes it before fitting.
5. Final-evaluation outcomes must not influence method, parameter, threshold, fixture,
   or policy choices.
6. This evidence remains synthetic. It does not imply model-serving, Kaggle, customer,
   or production evidence.

## Intended repository layout

The next implementation slice should create this root and no sibling alternative
layout:

```text
data/fixtures/synthetic_calibration_redesign/
  inputs/
    cases/
  expected_outcomes/
  scenario_family_registry.json
  manifest.json
  authoring_ledger.md
  rejected_case_ideas.md
```

### Asset roles

| Asset | Role | Allowed contents | Forbidden contents |
|---|---|---|---|
| `inputs/cases/*.json` | Runtime fixture input | Typed trace/context data, provenance, split, scenario-family identity, lawful confidence fields. | Observed labels, outcome-derived metrics, future-bearing values, retrospective optimal prefixes. |
| `expected_outcomes/*.json` | Evaluation-only outcome | Observed acceptance/survival labels and fixed expected assessment data. | Runtime-policy instructions, tuning directives, hidden configuration changes. |
| `scenario_family_registry.json` | Split and lineage control | Family ID, role, split, parent-family identity, source-template fingerprint, case IDs. | Mutable performance scores or promotion conclusions. |
| `manifest.json` | Integrity/provenance control | Hashes, byte counts, split counts, family inventory, fixture-set identity/version. | Raw secrets, private payloads, dynamically generated metrics. |
| `authoring_ledger.md` | Human review trail | Rationale, date, authoring constraints, accepted/rejected ideas. | Final-evaluation results used to justify design. |
| `rejected_case_ideas.md` | Anti-drift record | Rejected near-duplicates, ambiguous scenarios, leakage risks, non-diagnostic cases. | Unbounded brainstorming or hidden tuning notes. |

## Split and scenario-family contract

Each case must declare exactly one `scenario_family_id` and one `split`.

```text
allowed_splits=development, calibration, final_evaluation, adversarial_regression
```

### Required lineage fields

Every registry record must include:

```text
scenario_family_id
split
primary_data_role
parent_scenario_family_id
source_template_fingerprint
case_ids
rationale
is_final_evaluation_quarantined
```

Rules:

- `scenario_family_id` is unique within the fixture set.
- `primary_data_role` and `split` must agree.
- `parent_scenario_family_id` is either `null` or refers only to a family in the same
  split.
- `source_template_fingerprint` must not repeat across `calibration` and
  `final_evaluation` families.
- `is_final_evaluation_quarantined=true` is mandatory for all final-evaluation
  families.
- A case ID may appear in exactly one family and exactly one split.

## Proposed scenario-family registry

The following names define the minimum authoring inventory. They are scenario contracts,
not pre-authored outcome values.

| Family ID | Split | Primary role | Design property | Why it exists |
|---|---|---|---|---|
| `CRV1-CAL-BROAD-RANGE` | `calibration` | Fit evidence | Covers low, medium, and high confidence ranges with a stable, non-trivial probability mapping. | Supports fitting a global temperature parameter without one-bin shortcut behavior. |
| `CRV1-CAL-POSITIONAL-DECAY` | `calibration` | Fit evidence | Includes lawful confidence across candidate positions with gradual confidence decay. | Tests fit evidence beyond a single flat position regime. |
| `CRV1-DEV-CONTRACT-EDGE` | `development` | Loader and contract checks | Includes valid boundary-value fixtures and intentionally malformed companion ideas kept outside valid manifests. | Supports deterministic plumbing checks without entering fit or final assessment. |
| `CRV1-ADV-SPLIT-LEAKAGE` | `adversarial_regression` | Regression protection | Encodes prohibited cross-split lineage or source-template reuse. | Ensures fixture validation rejects leakage attempts. |
| `CRV1-FINAL-MIXED-RELIABILITY` | `final_evaluation` | Fresh final assessment | Uses a distinct scenario family with mixed confidence bands and independently authored outcomes. | Tests the frozen artifact outside calibration-family templates. |
| `CRV1-FINAL-ABRUPT-SUFFIX` | `final_evaluation` | Fresh final assessment | Uses a distinct abrupt-suffix behavior without reusing calibration templates. | Tests whether global calibration remains credible under a different trace shape. |

### Mandatory independence rules

The `CRV1-FINAL-*` families must not:

- derive from `CRV1-CAL-*` source templates;
- share a parent scenario family with `CRV1-CAL-*` families;
- reuse calibration case identifiers, seeds, token sequences, prompt skeletons, or
  outcome-generation procedures;
- be selected, removed, changed, or rebalanced after the calibrated artifact is fit;
- use `STF-004`, its labels, source pattern, or outcome values as an authoring input.

## Case-count and evidence floor

The next implementation must not claim that a small synthetic set establishes broad
calibration generalization. The goal is a diagnostic, governed proof boundary.

Minimum authoring floor:

```text
calibration_families>=2
calibration_cases_per_family>=3
final_evaluation_families>=2
final_evaluation_cases_per_family>=2
adversarial_regression_families>=1
development_families>=1
```

This gives a minimum of:

```text
calibration_cases>=6
final_evaluation_cases>=4
```

The implementation may exceed these counts only if every additional case has a clear
diagnostic purpose and a ledger entry. More cases are not automatically better; duplicate
or ambiguous cases must be rejected.

## Runtime-input contract requirements

Each valid runtime case must retain only information needed for lawful replay and later
calibration application. At minimum, preserve the existing typed trace and provenance
boundary, including:

```text
case_id
trace_id
split
scenario_family_id
source_type
workload_type
decode_round
block_position_index
visible_prefix_token_ids
conditional_survival_confidence
capacity_snapshot
fixture_set_id
fixture_set_version
```

The concrete schema must reuse or extend existing committed contracts rather than pass
untyped dictionaries.

Runtime case files must not contain:

```text
observed_acceptance
prefix_survival_label
target_acceptance_outcomes
verification_outcomes
retrospective_optimal_prefix
final_evaluation_metric
promotion_decision
```

## Expected-outcome contract requirements

Expected-outcome files must be structurally separate from runtime inputs and include the
post-hoc labels required for calibration assessment. Their exact model shape must be
implemented through strict Pydantic contracts in the next behavior-changing slice.

At minimum, each outcome asset must bind to:

```text
case_id
trace_id
split
scenario_family_id
fixture_set_id
fixture_set_version
observed_acceptance_labels
provenance_note
```

No expected-outcome file may alter the candidate method, fit configuration, promotion
criteria, or policy settings.

## Manifest requirements

`manifest.json` must be deterministic and include:

```text
fixture_set_id
fixture_set_version
source_type
runtime_input_root
expected_outcome_root
scenario_family_registry_path
split_counts
scenario_family_counts
file_inventory
file_sha256
file_byte_count
aggregate_sha256
authoring_protocol_version
```

Required manifest validation rules:

1. Every listed file exists and matches its declared hash and byte count.
2. Every case ID has one runtime input and one expected-outcome asset where outcomes are
   required by its role.
3. Runtime and outcome assets agree on `case_id`, `trace_id`, split, family, fixture-set
   identity, and version.
4. Calibration and final-evaluation scenario-family IDs are disjoint.
5. Source-template fingerprints are disjoint across calibration and final-evaluation.
6. Final-evaluation family records are marked quarantined.
7. All fixture assets are synthetic and public-safe.

## Authoring sequence

The implementation must follow this order:

1. Create and review the scenario-family registry without outcome values.
2. Create runtime input cases and expected-outcome files in separate directories.
3. Create the authoring ledger and rejected-case record.
4. Generate the manifest from final immutable bytes.
5. Add strict loader, manifest, split, and lineage validation tests.
6. Run the full suite and Ruff before staging.
7. Merge the fixture boundary before fitting any calibration artifact.

The following actions are prohibited during this sequence:

- reading or copying `STF-004` to guide new case construction;
- fitting `logit-temperature-scaling-v1` while fixture structure is still changing;
- modifying final-evaluation families after an artifact is fit;
- adding adaptive-policy code;
- adding capacity profiles or utility scoring;
- treating authoring success as calibration promotion.

## Required implementation tests

The subsequent behavior-changing fixture slice must include tests that prove:

1. A registry rejects duplicate case IDs across splits.
2. A registry rejects a scenario family assigned to more than one split.
3. A registry rejects a repeated source-template fingerprint across calibration and final
   evaluation.
4. A loader rejects runtime inputs containing evaluation-only fields.
5. A loader rejects runtime/outcome identity mismatches.
6. A manifest rejects altered files, hashes, counts, or aggregate hash mismatches.
7. Final-evaluation assets cannot be selected as calibration-fitting inputs.
8. `STF-004` is not a member of the new fixture-set manifest or registry.

## Acceptance gate before fitting

No calibration fitting is authorized until all of the following are true:

```text
- Fresh fixture assets are committed and manifest-verified.
- All split and lineage tests pass.
- Calibration and final-evaluation families are disjoint.
- Final-evaluation families are quarantined before artifact fitting.
- Candidate method remains logit-temperature-scaling-v1.
- Promotion criteria remain predeclared.
- Full repository pytest and Ruff checks pass.
```

## Claims permitted after fixture implementation

```text
- A fresh, synthetic, manifest-validated calibration evidence boundary exists.
- Scenario-family split isolation is enforced by registry and tests.
- Runtime inputs and expected outcomes remain structurally separated.
```

## Claims explicitly forbidden after fixture implementation

```text
- Temperature scaling improves calibration.
- Confidence is fit for automated scheduling.
- An adaptive policy exists or is authorized.
- A utility winner exists.
- Any real-model, Kaggle, serving, throughput, latency, cost, or production claim.
```

## Residual uncertainty

- The synthetic evidence floor may still be insufficient for strong generalization.
- The predeclared global temperature method may fail on the fresh final evaluation.
- Calibration success, if any, would still not prove scheduler utility.
- A later capacity-profile and policy-evaluation protocol remains required.
