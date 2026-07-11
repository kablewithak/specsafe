# SpecSafe Final PRD Acceptance Review

## Review status

```text
review_id=specsafe-final-prd-acceptance-v1
review_date=2026-07-11
governing_prd=docs/PRD.md version 1.2
review_status=ACCEPTED_FOR_V1_ENGINEERING_CLOSEOUT
highest_confirmed_evidence_level=public_replay_demo_released
production_serving_validated=false
```

This review maps the finished SpecSafe repository to the governing PRD. It closes the v1
engineering programme without reopening calibration research, reusing the consumed holdout,
republishing the Hugging Face Space, or adding serving infrastructure.

The acceptance decision is based on the committed architecture, ADRs, deterministic tests,
controlled reports, public Dataset receipt, public Space receipt, anonymous reconciliation, and
clean-main evidence retained before this closeout slice. The merge gate remains the final
non-mutating validation sequence in `docs/runbooks/specsafe-final-closeout.md`.

## Final decision

SpecSafe v1 is accepted as a:

> Research-grade, production-shaped policy evaluation harness with deterministic synthetic replay,
> supplemental small-model Kaggle evidence, a public bounded negative-evidence Dataset, and an
> anonymously reconciled read-only Hugging Face Space.

The project is not accepted as a production serving system. No production uptime, throughput,
latency, cost, load tolerance, customer-data safety, incident response, or operational ownership
claim is authorized.

## Governing invariants

| Invariant | Status | Evidence |
|---|---|---|
| Runtime decisions use only decision-time information. | `complete_with_evidence` | `src/specsafe/causal_safety/`, ADR-0002, causal-safety tests |
| Apparent utility gains fail when causal safety fails. | `complete_with_evidence` | unsafe retrospective control, comparison validity gates |
| Calibration and final evaluation remain separated. | `complete_with_evidence` | calibration manifests, holdout governance, ADR-0041 and ADR-0042 |
| Policies compare against identical traces and capacity profiles. | `complete_with_evidence` | matched replay harness and controlled Phase 5 report |
| Public artifacts exclude secrets, private data, and live input collection. | `complete_with_evidence` | publication candidates, receipts, anonymous reconciliation |
| Public claims do not exceed retained reproducible evidence. | `complete_with_evidence` | README, reports, Space evidence index, this review |

## Functional requirement matrix

### Contracts and provenance

| ID | Status | Acceptance evidence |
|---|---|---|
| FR-001 | `complete_with_evidence` | Pydantic v2 contracts under `src/specsafe/contracts/` cover core trace, calibration, capacity, policy, and report boundaries. |
| FR-002 | `complete_with_evidence` | Core models use strict validation, immutability, and unknown-field rejection with regression tests. |
| FR-003 | `complete_with_evidence` | Traces, profiles, calibration assets, policies, reports, candidates, and receipts carry stable IDs or manifest references. |
| FR-004 | `complete_with_evidence` | Evaluation artifacts retain trace, capacity, policy, configuration, and run identity fields. |
| FR-005 | `complete_with_evidence` | Core fixture evaluation runs repository-locally without an external model provider. |

### Causal safety

| ID | Status | Acceptance evidence |
|---|---|---|
| FR-010 | `complete_with_evidence` | Valid policies accept the approved causal scheduler context. |
| FR-011 | `complete_with_evidence` | Unapproved context types fail deterministically. |
| FR-012 | `complete_with_evidence` | Future, observed, and retrospective fields are rejected from valid runtime inputs. |
| FR-013 | `complete_with_evidence` | The unsafe retrospective context and policy remain isolated as evaluation-only controls. |
| FR-014 | `complete_with_evidence` | Comparison artifacts expose causal-safety status and violation details. |
| FR-015 | `complete_with_evidence` | Unsafe controls are excluded from valid comparisons and cannot support improvement claims. |

### Traces

| ID | Status | Acceptance evidence |
|---|---|---|
| FR-020 | `complete_with_evidence` | Versioned synthetic fixture sets are retained in the repository. |
| FR-021 | `complete_with_evidence` | Trace contracts preserve workload, split, provenance, round, position, confidence, labels, and capacity metadata. |
| FR-022 | `complete_with_evidence` | Runtime-visible fields are physically and contractually separated from post-hoc evaluation labels. |
| FR-023 | `complete_with_evidence` | Fixture validation rejects schema, provenance, split, and visible-prefix violations. |
| FR-024 | `complete_with_evidence` | Immutable fixture sets include manifests, counts, source class, generation notes, and hashes. |
| FR-025 | `complete_with_evidence` | Public evidence is sanitized and limited to permitted public or self-authored material. |

### Policies

| ID | Status | Acceptance evidence |
|---|---|---|
| FR-030 | `complete_with_evidence` | Fixed-length verification baseline implemented. |
| FR-031 | `complete_with_evidence` | Static confidence-threshold baseline implemented. |
| FR-032 | `complete_with_evidence` | Calibrated causal load-aware prefix policy implemented for controlled research. |
| FR-033 | `complete_with_evidence` | Intentionally unsafe retrospective policy retained as a negative control. |
| FR-034 | `complete` | No deployable oracle claim is made; any oracle use remains optional and evaluation-only. |
| FR-035 | `complete_with_evidence` | Valid policies emit typed verification decisions. |
| FR-036 | `complete_with_evidence` | Conservative fallback is implemented for unfit confidence. |

### Calibration

| ID | Status | Acceptance evidence |
|---|---|---|
| FR-040 | `complete_with_evidence` | Raw confidence reliability metrics are retained before calibration. |
| FR-041 | `complete_with_evidence` | Calibration fitting is limited to declared fit/calibration evidence. |
| FR-042 | `complete_with_evidence` | Raw and calibrated confidence were evaluated on held-out evidence. |
| FR-043 | `complete_with_evidence` | Brier, fixed-bin ECE, discrimination, per-position, and prefix-survival evidence are retained. |
| FR-044 | `complete_with_evidence` | Promotion and fitness gates were predeclared before the independent holdout replay. |
| FR-045 | `complete_with_evidence` | The failed Kaggle-derived candidate remains `KEEP_DIAGNOSTIC_ONLY`; conservative fallback is required. |

### Capacity

| ID | Status | Acceptance evidence |
|---|---|---|
| FR-050 | `complete_with_evidence` | Versioned synthetic capacity profiles are implemented. |
| FR-051 | `complete_with_evidence` | Light, moderate, saturated, and jagged conditions are retained. |
| FR-052 | `complete_with_evidence` | Kaggle-derived evidence is separately labelled and not conflated with synthetic profiles. |
| FR-053 | `complete_with_evidence` | Profile source, configuration, provenance, and units are recorded. |
| FR-054 | `complete_with_evidence` | Reports and public assets explicitly reject production-throughput interpretation. |

### Evaluation and reporting

| ID | Status | Acceptance evidence |
|---|---|---|
| FR-060 | `complete_with_evidence` | Named comparisons use identical immutable traces and profiles. |
| FR-061 | `complete_with_evidence` | Machine-readable result and evidence artifacts are retained. |
| FR-062 | `complete_with_evidence` | Human-readable Markdown reports are retained. |
| FR-063 | `complete_with_evidence` | Valid and causal-safety-invalid results remain separated. |
| FR-064 | `complete_with_evidence` | Neutral outcomes and the adaptive loss `MPC5-103` remain visible. |
| FR-065 | `complete_with_evidence` | Synthetic, Kaggle, public-demo, and production evidence classes are separated. |
| FR-066 | `complete_with_evidence` | Reports retain residual risks, non-claims, and next safe boundaries. |

### Public proof

| ID | Status | Acceptance evidence |
|---|---|---|
| FR-070 | `complete_with_evidence` | GitHub retains source, tests, ADRs, reports, experiment records, and runbooks. |
| FR-071 | `complete_with_evidence` | Governed Kaggle trace collection, runbooks, archives, diagnostics, and provenance are retained. |
| FR-072 | `complete_with_evidence` | Public Dataset is sanitized, versioned, ungated, hash-verified, and bound to a retained receipt. |
| FR-073 | `complete_with_evidence` | Public Space is a five-file prebuilt static replay surface with no live inference. |
| FR-074 | `complete_with_evidence` | Unsafe controls, mixed outcomes, and the failed confidence gate remain visible. |
| FR-075 | `complete_with_evidence` | The public Space and `docs/case-studies/specsafe-final-case-study.md` provide the case study; `docs/walkthroughs/specsafe-one-minute-walkthrough.md` provides the short walkthrough. |

## Non-functional acceptance

| Area | Status | Acceptance conclusion |
|---|---|---|
| Engineering standards | `complete_with_evidence` | Python 3.11+, typed boundaries, Pydantic v2, enums, deterministic tests, machine-readable artifacts, and provider-neutral core seams are retained. |
| Reproducibility | `complete_with_evidence` | Significant experiments retain IDs, hashes, source revisions, model/tokenizer metadata, seeds, configurations, timestamps, and evidence-class metadata. |
| Performance posture | `complete` | Local core evaluation remains CPU-capable; no application SLA or production-performance claim is made. |
| Maintainability | `complete_with_evidence` | Contracts, policies, profiles, replay, evaluation, reporting, and publication remain separated behind inspectable boundaries. |
| Privacy and security | `complete_with_evidence` | Public artifacts use minimized sanitized evidence; receipts contain no credential; anonymous reconciliation used no token. |

## Definition-of-done reconciliation

| PRD section | Status | Resolution |
|---|---|---|
| 28.1 Repository and architecture | `complete_with_evidence` | Clean-main evidence was retained before the slice; package boundaries are documented; README is updated by this slice; this review records final reconciliation. |
| 28.2 Causal correctness | `complete_with_evidence` | Approved context enforcement, forbidden-field rejection, unsafe negative control, and invalid-result blocking are retained. |
| 28.3 Data and reproducibility | `complete_with_evidence` | Versioned manifests, split controls, diagnostic fixtures, artifact identities, and local core evaluation are retained. |
| 28.4 Calibration | `complete_with_evidence` | Held-out metrics and fitness gates exist; the failed candidate is not promoted; fallback remains mandatory. |
| 28.5 Policy evaluation | `complete_with_evidence` | Fixed, threshold, and adaptive policies share frozen inputs; all required profiles and adverse cases are retained. |
| 28.6 Empirical and public proof | `complete_with_evidence` | Kaggle evidence, public Dataset, public static Space, case study, and walkthrough are present. |
| 28.7 Final maturity claim | `complete` | Maturity is bounded to research-grade, production-shaped, and public-replay-demo released. |

## Frozen outcome ledger

```text
adaptive_vs_fixed=2_wins_3_neutral_1_loss
adaptive_vs_threshold=3_wins_2_neutral_1_loss
adaptive_loss=MPC5-103
clearest_adaptive_wins=MPC5-104_MPC5-105
candidate_decision=KEEP_DIAGNOSTIC_ONLY
candidate_failure=ranking_safety_regression
candidate_promotion=closed_not_promoted
confidence_status=unfit_use_conservative_fallback
```

Public Dataset:

```text
repository_id=KaboKableMolefe/specsafe-bounded-negative-evidence-v1
published_revision=1ff151fc0646102f6e7b107d1bceb9a18e50098a
remote_file_count=9
anonymous_public_verification_passed=true
```

Public Space:

```text
repository_id=KaboKableMolefe/specsafe-reliability-lab
published_revision=453481cc16518ba8d8b425813aca4cfc74c2d0e8
remote_file_count=5
sdk=static
provider_side_build_required=false
anonymous_repository_verification_passed=true
anonymous_application_verification_passed=true
served_html_verified=true
credential_used_for_reconciliation=false
```

## Material deviations and reconciliations

### PRD historical maturity text

The PRD's Section 2.2 and post-V4 route text describe an earlier repository state. They remain
historical context, not the final status. This review, the accepted ADRs, committed artifacts,
publication receipts, and reconciliation evidence supersede those historical progress statements
without weakening the PRD's invariants.

### Public case-study requirement

The public Space already functions as a bounded technical case study. This closeout slice adds a
repository-native case study and a one-minute walkthrough so the PRD documentation requirement is
fully inspectable without depending on the Space's continued availability.

### Production validation

Production serving remains intentionally out of scope. This is not an unresolved v1 defect. It is a
preserved scope ceiling.

## Residual risks

- Anonymous reconciliation is point-in-time evidence, not a permanent uptime guarantee.
- The public provider may later change remote availability or platform behavior.
- The current Kaggle-derived confidence candidate remains unsafe for probability-driven activation.
- The consumed independent holdout cannot be reused for successor-method selection.
- Production operations, monitoring ownership, incident response, load testing, and customer-data
  validation remain unproven.

## Final non-claims

SpecSafe v1 does not prove:

- globally superior adaptive scheduling;
- a promotable confidence model, threshold, or scheduler;
- DSpark reproduction;
- live-traffic performance;
- production uptime, latency, throughput, cost reduction, or scale;
- customer-data safety or regulatory compliance;
- production readiness.

## Closeout gate

Run the exact non-mutating gate in:

```text
docs/runbooks/specsafe-final-closeout.md
```

Do not rerun the one-shot remote reconciliation writer. Do not republish or manually edit the
public Space as part of closeout.

## Post-closeout change control

SpecSafe v1 is closed after this slice merges and `main` is clean. Any successor calibrator,
serving experiment, customer-data route, or remote release change requires a new charter or ADR,
fresh independent evidence, and an explicit new authorization boundary.
