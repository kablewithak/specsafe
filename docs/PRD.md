# Product Requirements Document — SpecSafe

## Causal Confidence-Scheduled Verification Policy Lab

- **Document status:** Governing PRD — adopted and reconciled after V4 closeout
- **Version:** 1.2
- **Date:** 2026-07-07
- **Reconciliation basis:** ADR-0017 and repository audit at `main` commit `5c3fd8b`
- **Project owner:** Kabo Molefe
- **Repository:** `https://github.com/kablewithak/specsafe`
- **Primary branch:** `main`
- **Known repository baseline at authoring:** `989b024` — Merge pull request #1 from `feat/causal-information-boundary`
- **Primary implementation language:** Python 3.11+
- **Primary public title:** **SpecSafe: Causal Confidence-Scheduled Verification Policy Lab**
- **Repository description:** A research-grade lab for evaluating confidence-calibrated, load-aware LLM verification policies under explicit causal correctness constraints.
- **Project type:** Standalone research-grade side project. It is not a required dependency of the AI consultancy roadmap or its scheduled capstones.

---

## 1. Executive summary

SpecSafe is a research-grade, production-shaped policy-evaluation lab for one narrow question:

> Can an LLM verification scheduler spend limited verification compute more intelligently than blunt fixed rules while using only information available when each decision must be made?

The project is inspired by speculative-decoding systems research, especially the observation that a system can waste expensive target-model verification capacity by verifying long, low-probability suffixes indiscriminately. It is also motivated by the more important correctness warning: an optimizer can appear to improve a metric by using future candidate-token or verification-outcome information that was unavailable at decision time. In speculative decoding, this violates non-anticipation and can invalidate a losslessness guarantee. In SpecSafe, any policy result that depends on forbidden future information is rejected, regardless of apparent utility.

SpecSafe is deliberately **not** a DSpark reimplementation, a trained speculative drafter, a CUDA optimization project, a production model-serving engine, a vLLM/SGLang integration, or a live-traffic benchmark. The 50–70 hour budget is spent on a more defensible artifact: typed policy contracts, causal-safety gates, calibration, immutable trace replay, controlled capacity profiles, hard evaluation cases, negative controls, reproducible reports, a small-model Kaggle evidence layer, and a public Hugging Face replay lab.

The project’s finished proof is not “we made a model faster.” The finished proof is:

> Under explicitly defined trace-replay conditions, calibrated and causal verification-budget policies can be evaluated against fixed and threshold baselines; their operating conditions, negative cases, calibration fitness, and causal-validity status are visible, reproducible, and bounded by evidence.

---

## 2. Current repository facts and governing posture

### 2.1 Existing committed foundation

At PRD authoring, the repository already contains a real project foundation and a first causal-information control. The PRD governs future work from that actual baseline rather than from an imagined blank repository.

Known committed boundaries include:

- `README.md` defining the project identity, north star, scope ceiling, and phase model.
- `pyproject.toml` defining Python 3.11+, Pydantic v2, pytest, Ruff, and package metadata.
- `docs/PROJECT_CONSTITUTION.md` defining the absolute north star, core invariants, evidence posture, and release rule.
- `docs/adr/ADR-0001-project-boundary.md` establishing SpecSafe as a policy-evaluation lab rather than a serving engine.
- `docs/adr/ADR-0002-causal-information-boundary.md` establishing the causal runtime information boundary.
- `src/specsafe/contracts/models.py` containing strict Pydantic contracts including `CausalSchedulerContext`, `CapacitySnapshot`, `VerificationDecision`, and causal-safety result models.
- `src/specsafe/causal_safety/guard.py` requiring the exact approved runtime context type and rejecting retrospective or future-bearing context shapes.
- `src/specsafe/causal_safety/unsafe_controls.py` containing an intentionally invalid, evaluation-only retrospective context for negative-control tests.
- focused test modules for package metadata, causal context validation, and causal-safety behavior.

### 2.2 Current maturity statement

As reconciled after V4 closeout, SpecSafe is at:

> **Contracts enforced and synthetic-fixture validated.**
>
> The repository contains strict causal runtime contracts, separate runtime and post-hoc trace
> assets, fixed-length and static-threshold causal baselines, an isolated retrospective unsafe
> control, deterministic per-case synthetic replay, a descriptive baseline replay ledger, and
> multiple governed calibration programmes.
>
> The most recent V4 regularized-isotonic programme is closed as a valid negative held-out
> calibration result. Its Brier and ECE gates passed, but its ranking-safety gate failed. V4
> is therefore not eligible for adaptive-policy research, policy comparison, runtime control,
> refit, threshold tuning, rerun, or remediation in place.
>
> ADR-0018 now charters V5 as a fresh pre-fixture calibration eligibility programme with one
> fixed bounded monotone-beta method, a full held-out gate, and a hard stop rule. No V5 fixture,
> artifact, final assessment, scheduler, capacity-profile package, shared policy-utility scorer,
> cross-policy comparison report, Kaggle model experiment, Hugging Face replay demo, throughput
> result, or production-readiness claim exists yet.

The current maturity label is intentionally below `held-out replay evaluated`: SpecSafe has a
held-out **calibration** assessment, but it has not run a valid adaptive-versus-baseline policy
comparison on the same frozen replay inputs.

### 2.3 Governing operating posture

SpecSafe follows these operating rules throughout implementation:

1. **Policy validity is prior to policy utility.** A faster-looking policy is rejected if its decision uses forbidden information.
2. **Calibration is prior to automated probability-driven control.** Raw confidence may be evaluated, but it may not silently justify an adaptive scheduling claim before held-out calibration evidence exists.
3. **Immutable replay is prior to intervention claims.** Baselines and interventions must run against identical versioned traces and capacity profiles.
4. **Negative results are first-class evidence.** The project must preserve cases in which adaptive policies do not win.
5. **Core harness first; evidence amplification second.** Kaggle and Hugging Face strengthen the project only after the local deterministic harness is complete.
6. **No current test pass is treated as evidence of future system correctness.** Each new reliability claim requires its own specific tests and measurements.
7. **Public claims may not exceed reproducible evidence retained in the repository.**

---

## 3. Product identity, audience, and intended signal

### 3.1 Product identity

SpecSafe is a **policy-evaluation lab**. It is not an end-user chatbot or an inference service.

It accepts versioned traces containing scheduler-visible confidence and capacity metadata, applies one of several bounded verification policies, records typed decisions, and evaluates those decisions under a fixed evidence protocol.

### 3.2 Primary audiences

| Audience | What SpecSafe must make them believe | What they should be able to inspect |
|---|---|---|
| LLM systems engineer | The author understands speculative-decoding policy questions beyond superficial speed claims. | Causal contract, calibration method, scheduler inputs, negative controls, replay evaluation, assumptions. |
| AI hiring manager | The author can turn a current paper into a scoped, typed, tested, measurable engineering artifact. | Repository structure, ADRs, tests, explicit non-claims, report quality, design trade-offs. |
| Technical CTO | AI cost and latency policy decisions should be evaluated and governed, not tuned by intuition. | Fixed-versus-adaptive trade-offs, failure modes, risk controls, traceability, rollback posture. |
| Recruiter | This is an unusual and credible LLM systems project rather than a generic application demo. | README, concise case study, Hugging Face Space, Kaggle notebook, one-line project explanation. |
| Research-minded reviewer | Experimental claims are bounded, reproducible, and not contaminated by leakage or oracle information. | Data splits, manifests, seeds, policy rules, capacity-profile provenance, held-out report. |

### 3.3 Primary audience priority

1. LLM systems engineers
2. AI hiring managers
3. Technical CTOs
4. Recruiters
5. General public viewers

This order protects the project from being diluted into a dashboard-first portfolio item.

### 3.4 One-sentence public positioning

> SpecSafe is a DSpark-inspired policy evaluation lab for testing whether confidence-calibrated, load-aware verification policies reduce low-value inference work while preserving explicit causal correctness constraints.

---

## 4. Absolute north star

> **Build a reproducible lab that proves whether an LLM verification scheduler can spend limited compute more intelligently than blunt fixed rules, without using forbidden future information or breaking its correctness guarantee.**

Every feature, notebook, test, report, visualization, and public asset must support this statement.

### 4.1 The non-negotiable invariant

> **A valid runtime policy may never use information that was unavailable when its verification decision had to be made.**

If a policy decides whether to admit an early candidate position using a later sampled candidate token, a later target verification result, observed evaluation labels, or an after-the-fact optimal prefix, its result is invalid. That remains true if it appears to improve expected throughput, waste, latency, or another utility metric.

### 4.2 Scope decision rule

Every proposed addition must answer this question:

> Does this improve SpecSafe’s ability to prove that a calibrated, causal, capacity-aware verification policy is useful or safer than a blunt baseline under controlled evidence conditions?

- **Yes:** consider implementation.
- **No:** defer or reject.
- **Maybe, but it primarily beautifies a demo:** defer until the proof boundary is complete.
- **Improves a metric while weakening causal validity:** reject.

---

## 5. Problem statement

### 5.1 Technical problem

Autoregressive LLM generation is expensive because each new token normally requires a target-model computation. Speculative decoding can accelerate generation by having a draft process propose multiple candidate tokens and having a larger target model verify a candidate prefix. However, verification itself consumes valuable target-model capacity.

A fixed verification length is blunt:

- it may waste target capacity on low-confidence suffix tokens;
- it may be acceptable at low load but damaging at high concurrency;
- it does not account for workload type, such as structured text versus open-ended chat;
- it does not account for whether the underlying confidence signal is calibrated;
- it can encourage invalid optimization if a scheduler uses future-derived information.

### 5.2 Engineering problem

Many implementations blur three separate questions:

1. Is the draft or candidate quality strong enough?
2. Is the confidence signal reliable enough to drive a decision?
3. Is the scheduling policy useful and valid under capacity constraints?

SpecSafe separates them. A good draft does not prove a good scheduler. A high-ranking confidence signal does not prove calibration. A scheduler with a higher utility proxy does not prove validity if it violates causal non-anticipation.

### 5.3 Broader reliability problem

The same control problem appears outside literal speculative decoding:

- when to use a stronger model;
- when to run a second verifier;
- when to retrieve more evidence;
- when to rerank;
- when to retry;
- when to invoke a safety check;
- when to escalate to a human;
- when to refuse.

SpecSafe stays intentionally narrow in v1: **verification-budget scheduling over speculative-decoding-style traces**. It may later inform broader AI runtime policy evaluation, but that is not a v1 expansion license.

---

## 6. Research question, hypotheses, and evidence model

### 6.1 Primary research question

> Under controlled trace-replay conditions, does a calibrated, causal, load-aware verification policy improve defined policy utility relative to fixed-length and static-threshold baselines?

### 6.2 Secondary questions

1. Does post-hoc calibration improve the numerical reliability of confidence estimates on held-out traces?
2. Under which capacity regimes does adaptive scheduling reduce low-value verification work?
3. Under which workload types does adaptive scheduling help, fail to help, or become unnecessary?
4. What is the measurable cost of miscalibration?
5. Can an intentionally unsafe retrospective policy appear better by utility metrics while deterministically failing causal-safety controls?
6. What changes when capacity curves are smooth versus jagged?
7. How different are synthetic trace conclusions from small-model Kaggle evidence?

### 6.3 Hypotheses

| ID | Hypothesis | Required evidence |
|---|---|---|
| H1 | Post-hoc calibration improves probability reliability compared with raw confidence on held-out traces. | Before/after ECE, Brier score, reliability diagrams, and documented held-out split. |
| H2 | Under constrained capacity, a causal adaptive policy reduces low-value verification relative to a fixed-length policy. | Identical traces, identical capacity profiles, policy-comparison report, and predeclared utility metric. |
| H3 | Adaptive-policy value varies materially by workload type, calibration quality, and capacity regime. | Stratified report across structured text, code, open-ended chat, and multiple capacity profiles. |
| H4 | A retrospective look-ahead policy can improve apparent utility while failing causal correctness. | Deterministic negative-control fixture and causal-safety failure report. |
| H5 | Under light load or highly predictable workloads, fixed-long verification can remain competitive or win. | Preserved negative/neutral cases in the final report. |
| H6 | If confidence is unfit for automated scheduling, conservative fallback is safer than pretending probability estimates are usable. | Fitness gate tests and conservative-fallback outcomes. |

### 6.4 Evidence hierarchy

SpecSafe uses three evidence classes. Reports must label them explicitly.

| Evidence class | Meaning | Permitted claim |
|---|---|---|
| **Synthetic controlled evidence** | Deterministic traces and capacity profiles constructed to exercise specific behaviors. | The policy behaves in a specified way under controlled fixtures. |
| **Kaggle-measured evidence** | Small-model experiments and timing profiles captured in one documented Kaggle environment. | The policy behaved as measured in the recorded experimental environment. |
| **Production evidence** | Live serving, operational metrics, real workload distribution, monitored deployment. | Not available in v1 and must not be implied. |

---

## 7. Goals, non-goals, and non-claims

### 7.1 Product goals

SpecSafe v1 shall:

1. Define typed, schema-strict boundaries for all core policy inputs and outputs.
2. Enforce a causal information boundary before any runtime scheduling policy can run.
3. Provide immutable, versioned synthetic trace fixtures that support deterministic replay.
4. Implement fixed-length, static-threshold, causal load-aware, and intentionally unsafe retrospective policy controls.
5. Evaluate raw and calibrated confidence signals on held-out traces.
6. Model light, moderate, saturated, and jagged capacity profiles.
7. Produce machine-readable JSON results and human-readable Markdown reports.
8. Include negative cases where adaptive scheduling does not win.
9. Include an optional but planned same-tokenizer small-model Kaggle evidence layer.
10. Publish only sanitized, reproducible artifacts to GitHub, Hugging Face Dataset, and Hugging Face Space.
11. Make the causal-safety result visible in every policy comparison.

### 7.2 Non-goals

SpecSafe v1 will not:

- train a DSpark-style semi-autoregressive drafter;
- reproduce DSpark’s architecture, checkpoints, DeepSeek serving stack, or production results;
- implement custom CUDA kernels;
- operate as a production LLM server;
- integrate into vLLM, SGLang, TensorRT-LLM, or another serving engine;
- run a live queue or batch scheduler;
- provide a general model router;
- become a coding assistant product;
- add RAG, agents, vector databases, or tool execution to the core project;
- perform a benchmark sweep merely to maximize headline numbers;
- collect or publish client data, secrets, private prompts, private source code, or raw model payloads.

### 7.3 Explicit non-claims

SpecSafe must not claim:

- a production speedup;
- live-traffic performance;
- production-ready serving capability;
- DSpark reproduction;
- DeepSeek-equivalent hardware behavior;
- target-distribution preservation outside an exact, explicitly implemented and tested experimental setting;
- universal advantage of adaptive scheduling;
- generic LLM cost optimization for all workloads;
- deployment readiness without deployment, monitoring, security, incident response, load testing, and operational ownership evidence.

---

## 8. Product definition and system boundaries

### 8.1 Core system flow

```text
versioned trace fixture or Kaggle-exported trace
  -> trace validation and provenance check
  -> allowed confidence feature boundary
  -> calibration or calibration-fitness decision
  -> approved CausalSchedulerContext
  -> selected policy
  -> capacity-aware verification decision
  -> deterministic trace replay scoring
  -> causal-safety assessment
  -> machine-readable result + Markdown report
```

### 8.2 Three-system separation

SpecSafe must preserve three clean systems.

```text
Kaggle experiment layer
  -> same-tokenizer open-weight target/draft experiment
  -> trace collector and capacity measurements
  -> sanitized trace export + manifest

Core SpecSafe library
  -> contracts
  -> causal safety
  -> synthetic fixtures
  -> calibration
  -> scheduling
  -> capacity profiles
  -> trace replay
  -> evaluation
  -> reporting

Public proof layer
  -> GitHub source, tests, ADRs, reports
  -> Hugging Face Dataset with sanitized artifacts
  -> Hugging Face Space replay lab
  -> case study and walkthrough
```

### 8.3 Boundary rule

Notebook/model code may create trace artifacts. It must not become a hidden runtime dependency of core causal-safety tests or deterministic policy-replay tests. The core library must run locally against repository-versioned fixtures without credentials, a GPU, an internet connection, or a model download.

---

## 9. Terminology and conceptual model

| Term | Meaning in SpecSafe |
|---|---|
| Target model | The larger/reference model whose candidates are treated as the verification reference in an experiment. |
| Draft model | A smaller or degraded same-tokenizer candidate generator used to produce proposal traces. |
| Candidate position | A one-based position within a proposed speculative block. |
| Visible prefix | Candidate token IDs lawfully available before the current candidate position is considered. |
| Conditional survival confidence | A pre-sample estimate that the current candidate position survives verification, conditional on prior positions being accepted. |
| Prefix survival probability | The cumulative estimated probability that positions through a given point survive. |
| Verification budget | The number of candidate positions admitted for target verification for a request or batch. |
| Capacity profile | A declared relationship between verification workload and available progress/throughput proxy. |
| Causal scheduler | A policy that uses only lawful, decision-time information. |
| Retrospective scheduler | An evaluation-only, unsafe policy with access to future or observed information. |
| Calibration | A transformation or assessment that makes stated probabilities align more closely with observed frequencies. |
| Low-value verification | Verification spend whose expected marginal utility is insufficient under the active capacity condition. |
| Policy utility | A declared scoring function combining expected accepted work and capacity behavior. It is not a production throughput claim. |
| Negative control | A deliberately invalid or weak method included to demonstrate that the harness rejects flawed logic. |

---

## 10. Causal information contract

### 10.1 Principle

The causal contract is the core correctness boundary of SpecSafe.

A runtime scheduler receives only information that exists before the decision it is making. It may not receive the current sampled candidate token, any future candidate token, target acceptance/rejection outcomes, observed labels, retrospective best prefixes, or future-derived confidence values.

### 10.2 Approved runtime input

The only approved v1 runtime policy input is the exact `CausalSchedulerContext` type. Its established fields are:

- `trace_id`
- `request_id`
- `workload_type`
- `decode_round`
- `block_position_index`
- `visible_prefix_token_ids`
- `conditional_survival_confidence`
- `capacity_snapshot`

The contract is immutable and forbids unknown fields.

### 10.3 Allowed versus forbidden information

| Decision | Allowed | Forbidden |
|---|---|---|
| Admit position 1 | Request identity, workload metadata, empty or lawful prior prefix, pre-sample confidence for position 1, current capacity snapshot. | Current sampled token value, future sampled token values, current or future target outcome, post-hoc labels, retrospective optimal prefix. |
| Admit position k | Lawfully visible prefix of prior sampled positions, pre-sample confidence for k, prior lawful admissions, current capacity snapshot. | Candidate k’s sampled value before it is lawfully available, later candidates, later target outcomes, future-dependent confidence. |
| Stop or fallback decision | Current causal state, declared policy parameters, calibration-fitness state, capacity snapshot. | Future reward, actual eventual acceptance, post-hoc comparison result, oracle scheduling label. |
| Evaluation score | Full trace labels may be used after decisions are recorded. | Post-hoc labels may not be fed back into the same runtime decision. |

### 10.4 Enforcement requirements

The core library shall:

- require the exact approved runtime context type before policy execution;
- reject alternative model or object shapes, even if structurally similar;
- produce machine-readable `forbidden_future_information_access` failures where named forbidden fields are detected;
- retain an intentionally unsafe `RetrospectiveEvaluationContext` only for test and evaluation control purposes;
- never serialize or pass retrospective context to an approved runtime policy;
- test prefix-length consistency at every candidate position;
- test unknown-field rejection;
- test that the causal status is present in policy results.

### 10.5 What passing the causal boundary proves

Passing the causal boundary proves only this:

> The policy boundary does not expose named future or observed information to a valid runtime scheduler.

It does **not** alone prove full lossless speculative decoding, target-distribution preservation, serving correctness, or production safety.

---

## 11. Functional requirements

### 11.1 Contract and provenance requirements

| ID | Requirement |
|---|---|
| FR-001 | The system shall validate all core trace, capacity, calibration, policy, and report objects with Pydantic v2 contracts. |
| FR-002 | Core contracts shall be immutable and reject unknown fields. |
| FR-003 | Every trace, capacity profile, calibration artifact, policy configuration, and report shall carry a stable version identifier or manifest reference. |
| FR-004 | Every evaluation result shall record the trace-set ID, capacity-profile ID, policy ID, configuration hash, and run ID. |
| FR-005 | The core harness shall run with repository-local fixtures and no external model provider. |

### 11.2 Causal-safety requirements

| ID | Requirement |
|---|---|
| FR-010 | A valid policy shall receive only `CausalSchedulerContext`. |
| FR-011 | A runtime policy shall be rejected if passed an unapproved context type. |
| FR-012 | A runtime policy shall be rejected if its input exposes known future, observed, or retrospective fields. |
| FR-013 | The system shall retain a deliberate unsafe retrospective context and scheduler for negative-control evaluation only. |
| FR-014 | Every policy comparison report shall show causal-safety status and violation details where applicable. |
| FR-015 | A causal-safety failure shall invalidate policy-improvement claims in the report summary. |

### 11.3 Trace requirements

| ID | Requirement |
|---|---|
| FR-020 | The system shall load versioned synthetic trace fixtures from the repository. |
| FR-021 | Each trace shall identify workload type, split, model-pair/provenance metadata, decode round, candidate position, confidence inputs, observed labels used only during scoring, and required capacity metadata. |
| FR-022 | Trace schemas shall distinguish runtime-visible fields from evaluation-only labels. |
| FR-023 | The system shall reject trace fixtures with missing provenance, invalid split labels, invalid visible-prefix lengths, or schema violations. |
| FR-024 | Each immutable fixture set shall include a manifest with file hash, case count, split counts, source type, and generation notes. |
| FR-025 | Public fixtures shall contain only public/self-authored/licensed prompt material and minimized safe metadata. |

### 11.4 Policy requirements

| ID | Requirement |
|---|---|
| FR-030 | The system shall implement a fixed-length verification baseline. |
| FR-031 | The system shall implement a static confidence-threshold baseline. |
| FR-032 | The system shall implement a calibrated causal load-aware prefix policy. |
| FR-033 | The system shall implement an intentionally unsafe retrospective policy as an evaluation-only negative control. |
| FR-034 | The system may implement an oracle policy only as a clearly labelled evaluation upper bound; it must never be described as deployable. |
| FR-035 | All valid policies shall emit typed `VerificationDecision` records. |
| FR-036 | Valid policies shall have a conservative fallback state when confidence is judged unfit for automated scheduling. |

### 11.5 Calibration requirements

| ID | Requirement |
|---|---|
| FR-040 | The system shall compute raw confidence reliability metrics before calibration. |
| FR-041 | The system shall fit calibration only on the calibration split. |
| FR-042 | The system shall evaluate raw and calibrated confidence on a held-out final evaluation split. |
| FR-043 | The system shall report Expected Calibration Error, Brier score, a discrimination metric, per-position calibration, and prefix-survival calibration. |
| FR-044 | The system shall declare a preconfigured calibration-fitness criterion before evaluating the intervention. |
| FR-045 | When calibration is unfit, the adaptive policy shall emit `CONSERVATIVE_FALLBACK` rather than use untrusted probabilities as if they were calibrated. |

### 11.6 Capacity requirements

| ID | Requirement |
|---|---|
| FR-050 | The system shall support versioned synthetic capacity profiles. |
| FR-051 | Synthetic profiles shall include light, moderate, saturated, and jagged capacity conditions. |
| FR-052 | The system shall later support a separately labelled `KAGGLE_MEASURED` capacity profile source. |
| FR-053 | Capacity profiles shall record source, measurement/configuration metadata, and declared units. |
| FR-054 | Reports shall not describe synthetic or Kaggle-measured capacity behavior as production throughput. |

### 11.7 Evaluation and reporting requirements

| ID | Requirement |
|---|---|
| FR-060 | Every baseline and intervention shall run against the same immutable trace and capacity inputs for a named comparison. |
| FR-061 | The evaluation harness shall produce machine-readable results. |
| FR-062 | The evaluation harness shall produce a human-readable Markdown report. |
| FR-063 | Reports shall separate valid results from invalid causal-safety-failing results. |
| FR-064 | Reports shall include negative/neutral cases where the adaptive policy does not win. |
| FR-065 | Reports shall state synthetic, Kaggle-measured, and production evidence boundaries. |
| FR-066 | Reports shall include residual risks, non-claims, and next safe experiments. |

### 11.8 Public proof requirements

| ID | Requirement |
|---|---|
| FR-070 | The GitHub repository shall contain source, tests, ADRs, experiment documentation, reports, and reproducibility instructions. |
| FR-071 | A Kaggle notebook shall reproduce the small-model trace-collection experiment or explicitly record why the empirical layer was deferred. |
| FR-072 | A Hugging Face Dataset repository shall publish only sanitized, versioned trace fixtures and reports. |
| FR-073 | A Hugging Face Space shall replay precomputed traces and policies without needing live model inference. |
| FR-074 | The public demo shall display causal-safety failures rather than hiding them. |
| FR-075 | A case study and short walkthrough shall explain the system to technical and buyer audiences without overclaiming. |

---

## 12. Non-functional requirements

### 12.1 Engineering standards

- Python 3.11+.
- Full type hints on core public functions.
- Pydantic v2 at model/policy/report boundaries.
- No vague dictionary passing across core policy interfaces.
- Explicit enums for workload types, policy actions, profile sources, failure labels, and status fields.
- No blanket `except` handlers.
- Tests must be deterministic and avoid network/GPU dependencies in core library checks.
- JSON-safe, machine-readable result artifacts.
- Clean package boundaries aligned with the architecture map.
- Code must remain local-first and provider-neutral.

### 12.2 Reproducibility

Every significant experiment must record:

- experiment ID;
- source commit hash;
- Python version;
- package dependency lock/version record;
- model IDs and exact revisions when models are used;
- tokenizer ID and revision;
- seed(s);
- decoding settings;
- trace-manifest hash;
- calibration-manifest hash;
- capacity-profile hash;
- policy configuration hash;
- run timestamp;
- environment metadata appropriate to the evidence class;
- result artifact hash.

### 12.3 Performance posture

The core harness should be lightweight enough to run locally on CPU for fixture-based evaluation. It may be slower in Kaggle notebooks when collecting model evidence, but core evaluation must not depend on a GPU.

No performance SLA is claimed for the application itself. Runtime measurements are experimental evidence fields, not product availability guarantees.

### 12.4 Maintainability

The project shall favor the smallest architecture that can support the next three likely changes:

1. adding trace fields without breaking causal context;
2. adding a new valid policy without changing evaluation semantics;
3. adding a new capacity profile source without changing report contracts.

The project shall reject brittle designs that:

- bake fixture labels into policy logic;
- conflate calibration with final evaluation;
- couple notebook code to core scheduler tests;
- depend on a particular provider SDK in core packages;
- hide causal violations behind a generic exception;
- make future policy comparison outputs incomparable.

---

## 13. Data, models, and trace policy

### 13.1 Data policy

Permitted input sources:

- self-authored prompts;
- public benchmark prompts whose licenses permit the planned use;
- public model-generated traces derived from permitted prompts;
- synthetic diagnostic traces designed to test a named property.

Prohibited input sources:

- client prompts or documents;
- private code repositories;
- personal data;
- secrets, credentials, API tokens, session cookies, or environment dumps;
- non-public training outputs;
- raw model payloads larger or more sensitive than needed for the experiment.

### 13.2 Trace split policy

The project shall split at prompt/task level, not token level.

Required splits:

| Split | Purpose | May influence |
|---|---|---|
| Development / generation | Build trace plumbing and confidence features. | Implementation debugging only. |
| Calibration | Fit post-hoc confidence calibration. | Calibration parameters only. |
| Final evaluation | Score policy comparisons. | Nothing before final report generation. |
| Adversarial regression | Fixed special cases for known failure modes. | Regression protection only; not threshold tuning. |

A final evaluation prompt/task may not appear in the calibration split under a different token position or truncated continuation.

### 13.3 Small-model experiment selection criteria

The actual target/draft model pair is not chosen in this PRD. It must meet these hard criteria before the Kaggle phase begins:

1. **Same tokenizer and vocabulary.** Token-level probabilities and acceptance-style comparisons require compatible token spaces.
2. **Publicly accessible and license-compatible.**
3. **Small enough for a reproducible Kaggle GPU notebook.**
4. **Exact model revision can be pinned.**
5. **Draft/target roles are technically explainable.** A smaller same-family checkpoint or explicitly degraded draft control is acceptable; arbitrary unrelated models are not.
6. **Output logits or probability data needed by the trace collector are accessible.**
7. **No model choice is selected purely for a headline metric.**

### 13.4 Kaggle trace schema — minimum required fields

The final contract may evolve through ADR and schema versioning, but a Kaggle-exported trace must support at least:

```text
trace_id
case_id
split
workload_type
source_type
model_pair_id
target_model_id
target_model_revision
draft_model_id
draft_model_revision
tokenizer_id
tokenizer_revision
seed
decoding_configuration_id
decode_round
block_position_index
visible_prefix_token_ids
candidate_token_id
draft_probability
target_probability
raw_confidence
conditional_acceptance_label
prefix_survival_label
draft_entropy
target_entropy
runtime_metadata
trace_schema_version
```

The runtime policy contract must remain narrower than the full trace schema. Evaluation labels and target outcomes are retained for post-hoc scoring only.

### 13.5 Data minimization and publication

Public trace outputs should prefer:

- token IDs over raw prompts where raw text is unnecessary;
- safe, short self-authored excerpts when text is needed for explanation;
- aggregate confidence and outcome metrics over full vocabulary logits;
- manifests and hashes over raw large artifacts;
- documented sampling/configuration metadata over unnecessary payload duplication.

---

## 14. Policy definitions

### 14.1 Fixed-length baseline

**Purpose:** Establish a simple blunt policy.

The fixed-length policy admits a configured number of candidate positions per request regardless of confidence, workload type, or capacity regime.

It must expose:

- `policy_id`;
- configured maximum verification length;
- action and reason per candidate position;
- typed decision trace;
- no hidden access to evaluation labels.

### 14.2 Static confidence-threshold baseline

**Purpose:** Establish a confidence-aware but capacity-blind policy.

The static-threshold policy admits candidate positions while the valid pre-sample confidence meets a configured threshold.

It may use only approved causal context. It may not use capacity to alter its threshold in v1.

### 14.3 Calibrated causal load-aware prefix policy

**Purpose:** Primary intervention.

The policy shall:

1. receive lawful causal context only;
2. use a calibrated estimate of conditional survival confidence;
3. compute or consume valid prefix-survival estimates;
4. consider an explicitly declared capacity profile;
5. decide whether the marginal expected utility of admitting the next position is sufficient;
6. emit `ADMIT`, `STOP`, or `CONSERVATIVE_FALLBACK`;
7. retain a traceable reason code;
8. stop or fall back when calibration fitness is insufficient.

The v1 policy does not need to solve a global production scheduling problem. It needs to be deterministic, inspectable, and evaluable under declared replay assumptions.

### 14.4 Unsafe retrospective policy

**Purpose:** Negative control.

The unsafe policy may be constructed so that it can see:

- future candidate token IDs;
- future acceptance outcomes;
- observed labels;
- retrospective optimal prefix;
- future-derived confidence.

It must be clearly marked `evaluation_only` and must fail causal-safety checks. It exists to demonstrate that apparent utility is not enough.

### 14.5 Oracle upper bound — optional

An oracle may be included later to show a post-hoc upper bound. It must:

- be isolated from valid runtime policies;
- be labelled non-deployable;
- never participate in a valid intervention claim;
- not be allowed to tune thresholds on final evaluation data without explicit disclosure.

---

## 15. Calibration and confidence-fitness design

### 15.1 Why calibration is mandatory

A confidence score can rank easier and harder candidates well while remaining numerically wrong. A scheduler that treats an overconfident `0.95` as a true 95% survival probability may spend capacity incorrectly.

SpecSafe therefore distinguishes:

- **discrimination:** whether the score separates likely-good and likely-bad candidates;
- **calibration:** whether the stated probability matches observed frequency;
- **policy fitness:** whether the calibrated confidence is sufficiently reliable for the policy’s intended use.

### 15.2 Calibration methods

The first implementation should prefer a simple, explainable post-hoc method. Candidate methods may include temperature scaling or isotonic regression, subject to the actual trace distribution and data volume.

Selection rule:

> Use the simplest calibrated transformation that is stable, documented, held-out evaluated, and does not obscure the confidence boundary.

### 15.3 Required metrics

| Metric | Purpose |
|---|---|
| Expected Calibration Error (ECE) | Measures mismatch between predicted confidence and observed frequency across bins. |
| Brier score | Measures probability quality as a proper scoring rule. |
| ROC-AUC or equivalent discrimination metric | Measures ranking quality separately from calibration. |
| Reliability diagram | Makes overconfidence/underconfidence visually inspectable. |
| Per-position calibration | Tests whether calibration changes across candidate positions. |
| Prefix-survival calibration | Tests whether cumulative conditional estimates remain usable for prefix scheduling. |
| Coverage / sample count by bin | Prevents visual conclusions from sparse bins. |

### 15.4 Calibration-fitness gate

Before an adaptive policy can be presented as a valid calibrated policy, the report must include a predeclared calibration-fitness decision.

The fitness configuration must define:

- selected metric thresholds or comparative requirements;
- minimum sample count;
- whether performance must improve over raw confidence;
- response to failure;
- configuration version and hash.

Failure response:

```text
confidence_not_fit_for_automated_scheduling
  -> adaptive policy does not make probability-driven admissions
  -> conservative fallback applies
  -> report marks adaptive policy claim unavailable for that condition
```

This project does not need to claim a universal numeric calibration threshold. It must define and enforce its own declared test threshold before observing the final evaluation result for that run.

---

## 16. Capacity-profile design

### 16.1 Capacity is an explicit model

SpecSafe shall never treat capacity as invisible magic. Every policy result must name the capacity profile used.

A capacity profile represents a declared relationship between verification batch workload and a progress/throughput proxy. It is not automatically a measured hardware truth.

### 16.2 Required synthetic profiles

| Profile | Intended behavior |
|---|---|
| `light_load` | Extra verification is relatively cheap; longer budgets may be reasonable. |
| `moderate_load` | Marginal verification cost begins to matter. |
| `saturated_load` | Extra verification sharply competes for constrained capacity. |
| `jagged_capacity` | Capacity curve includes discontinuities to test greedy-policy brittleness. |
| `flat_capacity_control` | Useful control where extra verification carries little modeled marginal penalty. |

### 16.3 Kaggle-measured profile

The Kaggle phase may capture controlled timing under a specified model, device, batch size, sequence length, and notebook environment.

The evidence must be labelled:

> Kaggle-measured experimental capacity profile. It is environment-specific and not a production serving benchmark.

### 16.4 Capacity units and utility

A capacity profile must define its units. Examples may include:

- model-forward steps per second;
- simulated verification tokens per decision interval;
- normalized capacity points;
- experimentally measured per-step latency.

The report shall state the exact utility formula used for each comparison. If the utility is a proxy, it must be labelled a proxy.

---

## 17. Evaluation design

### 17.1 Evaluation principle

A valid policy comparison uses:

- identical immutable traces;
- identical capacity profile;
- identical scorer;
- explicit policy configuration;
- causal-safety assessment;
- separate calibration and final evaluation data;
- preserved negative results.

### 17.2 Required workload classes

| Workload class | Reason |
|---|---|
| `structured_text` | Tests predictable, constrained continuations and high-confidence regimes. |
| `code` | Tests locally dependent, structured technical generation where candidate quality may differ from chat. |
| `open_ended_chat` | Tests higher-entropy and likely faster confidence-decay regimes. |

### 17.3 Required hard cases

The synthetic suite must include diagnostic fixtures for:

- raw confidence overestimation;
- raw confidence underestimation;
- confidence decay by candidate position;
- abrupt suffix failure;
- high-confidence long-prefix case;
- low-confidence early-stop case;
- light-load case where long verification is acceptable;
- saturated case where pruning is valuable;
- jagged curve case where simple greedy behavior is stressed;
- static-threshold-wins case;
- fixed-long-wins case;
- calibration-unfit conservative-fallback case;
- causal look-ahead counterexample;
- request competition with uneven marginal value;
- schema-invalid trace case;
- split-leakage rejection case.

### 17.4 Required metrics

#### Draft and trace quality

- agreement or acceptance-style survival by position;
- conditional survival rate by position;
- prefix-survival distribution;
- workload-stratified trace counts.

#### Calibration

- ECE;
- Brier score;
- discrimination metric;
- reliability diagram;
- per-position reliability;
- prefix reliability.

#### Cost/capacity proxies

- verification positions admitted;
- verification budget consumed;
- low-value verification count/rate;
- capacity proxy consumed;
- normalized latency proxy where appropriate.

#### Policy utility

- expected accepted work;
- declared expected utility;
- throughput proxy if defined;
- policy decision mix: admit/stop/fallback;
- utility by workload and profile.

#### Correctness and safety

- causal-safety pass/fail;
- count of forbidden-information attempts;
- invalid-policy exclusion rate;
- trace/provenance schema failure count.

#### Reproducibility

- deterministic replay consistency;
- manifest hash match;
- configuration hash match;
- result artifact hash.

### 17.5 Evaluation sequence

1. Validate trace and manifest schema.
2. Confirm split eligibility.
3. Fit calibration on calibration split only.
4. Freeze calibration configuration.
5. Evaluate calibration on held-out evaluation traces.
6. Determine calibration fitness.
7. Run valid baselines and valid adaptive policy over the same inputs.
8. Run unsafe negative control separately and mark it invalid.
9. Generate metrics and report.
10. Apply regression gate and non-claim review.

### 17.6 Invalid comparison conditions

A comparison is invalid if any of the following occurs:

- calibration is fit or tuned on final evaluation traces;
- a policy receives future or observed outcome fields;
- policies run on different trace files or capacity profiles without explicit stratification;
- trace manifest hash does not match expected input;
- policy configuration is missing;
- output report suppresses causal-safety status;
- a production claim is derived from synthetic or Kaggle-only evidence;
- an oracle policy is described as a deployable scheduler;
- a workload result is generalized beyond its evidence class.

---

## 18. Failure taxonomy

The final enum names may evolve through reviewed contract changes, but the evaluation/reporting taxonomy must cover at least:

| Failure label | Meaning |
|---|---|
| `forbidden_future_information_access` | Runtime policy input exposes future, observed, or retrospective information. |
| `unapproved_runtime_context_type` | A policy receives a context shape other than the approved causal contract. |
| `invalid_visible_prefix` | Prefix state and candidate position are inconsistent. |
| `trace_schema_error` | Trace does not conform to required schema. |
| `trace_manifest_mismatch` | Trace file does not match declared manifest/hash. |
| `evaluation_split_leakage` | Evaluation data influenced calibration or policy tuning improperly. |
| `model_pair_tokenizer_mismatch` | Draft and target pair are not appropriate for token-level experiment interpretation. |
| `miscalibrated_confidence` | Raw or calibrated probabilities do not meet declared fitness requirements. |
| `confidence_not_fit_for_automated_scheduling` | Adaptive probability-driven decisions are blocked in favor of conservative behavior. |
| `overconfident_scheduler` | Scheduler allocates based on probabilities that overstate observed survival. |
| `underconfident_scheduler` | Scheduler prematurely stops despite adequate observed survival. |
| `verification_waste` | Verification spend is allocated to low marginal-value positions under declared conditions. |
| `capacity_saturation` | Capacity regime prevents intended verification allocation. |
| `policy_instability` | Small profile/configuration changes cause disproportionate policy flips. |
| `unsupported_capacity_claim` | Report attempts to make a claim stronger than capacity evidence supports. |
| `report_provenance_missing` | Required evidence/configuration metadata is absent. |

---

## 19. Architecture and package requirements

### 19.1 Target package structure

The repository currently contains the first package seams. Future work shall evolve toward:

```text
specsafe/
  src/specsafe/
    contracts/
    causal_safety/
    traces/
    calibration/
    capacity_profiles/
    scheduling/
    trace_replay/
    eval_harness/
    reporting/
  data/
    fixtures/
    processed/
  notebooks/
    kaggle/
  scripts/
  tests/
  docs/
    adr/
    architecture/
    experiments/
    reports/
    case_study/
  README.md
  pyproject.toml
```

### 19.2 Dependency direction

```text
fixtures / Kaggle exports
  -> traces
  -> contracts
  -> calibration
  -> capacity profiles
  -> causal-safety guard
  -> scheduling
  -> trace replay
  -> evaluation harness
  -> reporting
```

Rules:

- `scheduling` must not import notebook code.
- `causal_safety` must not import model-provider or Kaggle code.
- `reporting` must not mutate policy state.
- `eval_harness` may score full labels after decisions, but those labels may not flow back into runtime policy context.
- public UI code must call the core replay/reporting APIs rather than reimplement policy logic.

### 19.3 Error handling

Core failures must be explicit and typed where possible. Avoid silent fallback. If a policy cannot make a valid calibrated decision, it must emit an explicit conservative-fallback result with a reason code.

---

## 20. Privacy, security, and publication controls

### 20.1 Default controls

- Data minimization: retain only fields needed for trace replay, calibration, and reports.
- No PII or secrets in traces, logs, fixtures, screenshots, notebook outputs, or public reports.
- No raw private prompts or raw client artifacts.
- Environment separation: local development, Kaggle experiment, and public Hugging Face artifacts are separate boundaries.
- Least privilege: credentials, if ever required for hosted model access, are supplied through platform-specific secret mechanisms and never committed.
- Ignore `.env`, model caches, raw experimental outputs, notebooks checkpoints, and local artifacts through `.gitignore`.
- Maintain an auditable source/provenance note for public data and model artifacts.

### 20.2 Kaggle controls

- Use Kaggle secret controls for any necessary token.
- Do not print secret values.
- Do not publish raw notebook outputs containing credentials, local paths, or unexpected payloads.
- Freeze or export sanitized artifacts intentionally rather than publishing the entire working directory.

### 20.3 Hugging Face controls

- Dataset repository contains only sanitized fixtures, manifests, reports, and allowed visualizations.
- Space uses precomputed artifacts and no secret-dependent model inference in v1.
- Space displays evidence boundaries and non-claims prominently.

### 20.4 Compliance posture

SpecSafe is a public research/portfolio project, not a client processing system. The project applies engineering controls aligned with minimization, redaction, retention discipline, least privilege, environment separation, and vendor-boundary awareness. It does not provide legal advice.

---

## 21. Phase plan, time budget, and exit gates

### 21.1 Time budget

Total target budget: **50–70 hours**.

The project may not spend the majority of its time on Kaggle or UI. At least 20–25% of time is reserved for tests, evaluation, reports, documentation, and public proof packaging.

### 21.2 Phases

| Phase | Name | Reconciled status | Deliverable / retained evidence | Next gate |
|---|---|---|---|---|
| 0 | Repository and project constitution | Complete | Public repository, package scaffold, constitution, ADR-0001. | None. |
| 1 | Contracts and causal-information boundary | Complete | Strict Pydantic contracts, exact-type runtime guard, ADR-0002, and unsafe negative control. | Preserve exact causal boundary. |
| 1.5 | PRD adoption and reconciliation | Complete | PRD adopted; v1.1 reconciles historical phase wording with V4 closeout and audited source. | Keep PRD status aligned after material programme changes. |
| 2 | Synthetic traces, valid baselines, and deterministic replay | Complete for the required foundation | Versioned fixtures; fixed-length and static-threshold policies; isolated unsafe control; deterministic per-case replay; descriptive development/adversarial baseline ledger. | Preserve immutable shared-input replay semantics. |
| 3 | Calibration and confidence fitness | V4 closed negative; V5 chartered pre-fixture | ADR-0018 fixes a new V5 evidence namespace, bounded monotone-beta method, complete final gate, fallback, and hard stop rule. | Implement V5 typed artifact and final-assessment contracts plus non-final gate tests before any V5 evidence is authored. |
| 4 | Causal load-aware scheduler | Not implemented | No audited causal adaptive scheduler consumes capacity and calibrated confidence together. | A successor calibration gate must pass before scheduler implementation is authorized. |
| 5 | Shared policy comparison and reports | Incomplete | Per-case replay exists, but no capacity-profile package, utility scorer, cross-policy comparator, or valid adaptive-versus-baseline report exists. | Build only after a valid adaptive policy exists. |
| 6 | Kaggle small-model evidence | Not started | No committed Kaggle notebook or measured capacity profile. | Local core policy comparison must be complete first. |
| 7 | Public proof release | Not started | No Dataset, Space, or public replay pack. | Deterministic reports and public-safe retained artifacts must exist first. |
| 8 | Final reconciliation and handover | V4 closeout complete; project-wide completion pending | V4 handover and ADR-0017 reconcile the current route. | Complete only after the evidence ladder is satisfied. |

### 21.3 Core completion boundary

The core research proof is complete only after Phase 5 produces a valid same-input comparison
between a causal adaptive policy and the named blunt baselines.

Phase 2 is not a blocker: its synthetic baseline and replay foundation is implemented. The active
blocker is the absence of an eligible calibrated adaptive-policy path after V4's ranking-safety
regression. ADR-0018 now constitutes one fresh V5 eligibility programme, but V5 may not create
fixture evidence until its typed artifact, assessment contract, and non-final complete-gate tests
are merged. It must not use V4 final evidence as a tuning input.

Phases 6 and 7 are evidence amplification and public packaging. They are valuable but must not
mask an incomplete local policy-comparison harness.

### 21.4 Stop gates

- Do not start Kaggle model work until synthetic trace replay, causal safety, and baseline policies work locally.
- Do not make adaptive-policy claims until calibration is evaluated on held-out traces.
- Do not build a Hugging Face Space until reports can be generated deterministically from local fixtures.
- Do not add model-serving features because the lab does not yet have a serving-engine proof requirement.
- Do not start a new adjacent project before Phase 5 core proof is complete unless explicitly reprioritized.

---

## 22. Kaggle experiment plan

### 22.1 Purpose

Kaggle is an evidence acquisition environment. It is not the product and must not become the only way the project works.

The Kaggle experiment aims to produce:

- same-tokenizer target/draft evidence traces;
- candidate-position agreement/acceptance-style observations;
- raw confidence features;
- per-position confidence behavior;
- controlled environment timing measurements;
- an environment-specific capacity curve;
- sanitized, versioned exports suitable for core replay.

### 22.2 Required notebook properties

The Kaggle notebook shall include:

- exact package versions;
- model and tokenizer IDs and revisions;
- seed configuration;
- prompt/source provenance;
- decoding configuration;
- trace schema version;
- export manifest creation;
- no secrets printed in cells or outputs;
- clear separation between raw intermediate data and publishable sanitized artifacts;
- a final limitations section.

### 22.3 Kaggle non-claims

The notebook must state:

- it does not train DSpark;
- it does not reproduce DeepSeek serving;
- it does not establish live-concurrency behavior;
- it does not establish production throughput;
- timing measurements are specific to its captured environment;
- trace agreement alone does not establish lossless speculative decoding.

---

## 23. Hugging Face publication plan

### 23.1 Hugging Face Dataset repository

The Dataset repository should contain:

- sanitized synthetic trace fixtures;
- sanitized Kaggle-derived trace exports, if published;
- manifests and hashes;
- calibration artifacts;
- machine-readable policy results;
- Markdown reports;
- a dataset card describing source, schema, splits, limitations, and non-claims.

### 23.2 Hugging Face Space

The Space is a **replay lab**, not a live model-serving demo.

Required panels:

1. **Policy Playground**
   - select a trace fixture and capacity profile;
   - compare fixed, threshold, and causal adaptive policies;
   - display actions, budget, expected utility proxy, and causal status.

2. **Calibration Lab**
   - raw versus calibrated reliability charts;
   - ECE/Brier/discrimination values;
   - per-position behavior.

3. **Capacity Sensitivity**
   - light, moderate, saturated, and jagged profile comparison;
   - clearly labelled synthetic versus Kaggle-measured profiles.

4. **Causal Failure Demo**
   - show unsafe retrospective policy;
   - show apparent utility;
   - show causal-safety fail result;
   - explain why the result cannot support a valid claim.

5. **Evidence Boundaries**
   - what the project demonstrates;
   - what it does not demonstrate;
   - link to source, report, and dataset manifest.

### 23.3 Space non-functional requirements

- Runs CPU-only against precomputed artifacts in v1.
- Does not require user credentials.
- Does not run live model inference.
- Does not retain user inputs.
- Shows fixed demo data and local calculations only.

---

## 24. Documentation and reporting requirements

### 24.1 Required documentation

- README with current maturity, local run instructions, architecture, and scope ceiling.
- ADRs for significant irreversible decisions.
- Experiment design document.
- Trace schema documentation.
- Calibration methodology note.
- Capacity-profile methodology note.
- Evaluation protocol and failure taxonomy.
- Kaggle notebook README.
- Hugging Face Dataset card.
- Hugging Face Space evidence-boundary page.
- Case study.
- One-minute walkthrough script.

### 24.2 Required report sections

Every significant report must include:

1. Objective and hypothesis.
2. Evidence class.
3. Input trace and profile manifests.
4. Policy configurations.
5. Calibration status.
6. Causal-safety status.
7. Main metrics.
8. Breakdown by workload and capacity regime.
9. Negative/neutral cases.
10. Failure taxonomy summary.
11. Residual risks.
12. Non-claims.
13. Reproduction command or procedure.

### 24.3 Report validity marker

A report must visibly mark one of:

```text
VALID_COMPARISON
INVALID_CAUSAL_COMPARISON
INVALID_SPLIT_LEAKAGE
INVALID_PROVENANCE
CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY
```

No report may headline a utility comparison without a validity marker.

---

## 25. Testing strategy

### 25.1 Test layers

| Layer | Purpose |
|---|---|
| Contract unit tests | Schema strictness, enums, field validation, immutability, unknown-field rejection. |
| Causal-safety tests | Exact-type enforcement, forbidden-context rejection, negative controls. |
| Fixture validation tests | Manifest, schema, split, and provenance checks. |
| Policy unit tests | Fixed, threshold, adaptive, fallback, and unsafe behavior. |
| Calibration tests | Split separation, metric calculations, fit/transform determinism. |
| Replay integration tests | Same traces and profiles yield reproducible comparable outputs. |
| Regression tests | Known causal counterexample, known calibration failure, known capacity edge case. |
| Report tests | Required metadata and validity markers appear in outputs. |

### 25.2 Minimum regression fixtures

At minimum, preserve:

- the causal look-ahead counterexample;
- a schema-invalid future-field context;
- calibration leakage attempt;
- high-confidence/light-load case;
- low-confidence/saturated case;
- jagged capacity case;
- adaptive-policy-loses case;
- calibration-unfit fallback case.

### 25.3 Test discipline

- One test module per meaningful boundary where practical.
- No test depends on Kaggle execution or internet access.
- Use fixed seeds for any randomized synthetic generation.
- Preserve failing seed/configuration identifiers in regression reports.
- Do not change fixtures silently to make a policy appear better.

---

## 26. Risks, mitigations, and kill criteria

### 26.1 Major risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| Scope creep into serving infrastructure | Consumes the budget and weakens proof quality. | ADR-0001 scope ceiling; phase stop gates; reject custom kernel/server work. |
| Calibration leakage | Produces fake confidence improvement. | Prompt-level split manifest; separate calibration/final evaluation; tests. |
| Causal leakage | Makes a policy invalid while appearing stronger. | Exact causal runtime type; unsafe negative control; deterministic guard tests. |
| Model-pair incompatibility | Weakens token-level experiment interpretation. | Same-tokenizer requirement and model-selection gate. |
| Kaggle friction | Delays core project. | Kaggle starts after Phase 5; synthetic harness remains primary. |
| UI-first temptation | Produces a polished but weak demo. | Hugging Face Space starts only after deterministic reports exist. |
| Overclaiming | Damages credibility. | Evidence hierarchy, non-claims, report validity markers. |
| Weak hard cases | Allows trivial policy wins. | Diagnostic fixture constitution and negative cases. |
| Capacity-model overinterpretation | Synthetic curve mistaken for production measurement. | Explicit source labels and report language controls. |
| Data leakage/privacy mistakes | Public project risk. | Public/self-authored data only, minimization, no raw sensitive payloads. |

### 26.2 Kill/defer criteria

Defer or kill an addition if it:

- does not strengthen causal validity, calibration evidence, policy evaluation, or public proof;
- requires a serving engine before the core replay harness is complete;
- introduces provider lock-in into the core package;
- prevents local fixture-based execution;
- requires client or private data;
- creates a claim that cannot be measured and reproduced;
- turns the project into a generic dashboard;
- duplicates the planned AI consultancy roadmap capstones without creating distinct systems evidence.

---

## 27. Commercial and career translation

### 27.1 Portfolio translation

SpecSafe should support this truthful portfolio statement:

> Built a research-grade policy evaluation harness for confidence-calibrated, load-aware LLM verification scheduling, with causal non-anticipation checks, deterministic trace replay, negative controls, and explicit evidence boundaries.

### 27.2 Consultancy translation

SpecSafe is not sold as “speculative decoding consulting” to every company. Its broader proof value is:

> AI runtime decisions about when to spend more compute, verify, retry, escalate, or stop should be calibrated, evaluated, traceable, and constrained by explicit safety invariants.

Potential future service translation:

- **AI Inference Policy Reliability Audit**
- **Runtime Policy Hardening Sprint**
- **AI System Evaluation Audit module**

### 27.3 Boundary for commercial claims

SpecSafe does not prove that the author has optimized a client’s GPU serving stack. It demonstrates capability in evaluating and governing runtime decision policies under defined evidence conditions.

---

## 28. Acceptance criteria and definition of done

SpecSafe v1 is complete only when all of the following are true.

### 28.1 Repository and architecture

- [ ] `main` is clean and all work is merged through reviewable branches.
- [ ] The repository contains documented package boundaries for contracts, causal safety, traces, calibration, capacity profiles, scheduling, replay, evaluation, and reporting.
- [ ] The README reflects final maturity accurately.
- [ ] The PRD is reconciled with actual implementation and any material deviations are documented.

### 28.2 Causal correctness

- [ ] Valid runtime policies accept only the approved causal context.
- [ ] Unknown/future/observed/retrospective fields are rejected.
- [ ] An intentionally unsafe retrospective control deterministically fails causal-safety tests.
- [ ] Invalid causal results cannot be reported as valid improvements.

### 28.3 Data and reproducibility

- [ ] Trace schema and manifests are versioned.
- [ ] Splits are prompt/task-level and leakage checks exist.
- [ ] Synthetic fixtures include all required diagnostic cases.
- [ ] Every report identifies input artifacts and configuration hashes.
- [ ] Core evaluation runs locally without network, secrets, GPU, or model download.

### 28.4 Calibration

- [ ] Raw and calibrated confidence are evaluated on held-out data.
- [ ] ECE, Brier, discrimination, reliability visualizations, per-position, and prefix metrics are available.
- [ ] Calibration-fitness gate is configured and tested.
- [ ] Conservative fallback occurs when confidence is unfit.

### 28.5 Policy evaluation

- [ ] Fixed-length and static-threshold baselines run on identical fixtures.
- [ ] Valid causal load-aware policy runs on identical fixtures.
- [ ] Capacity profiles include light, moderate, saturated, and jagged conditions.
- [ ] Reports preserve cases where adaptive scheduling does not win.
- [ ] At least one constrained-capacity case supports a bounded adaptive-policy advantage.
- [ ] No result is generalized beyond its evidence class.

### 28.6 Empirical and public proof

- [ ] Kaggle notebook is reproducible or the empirical phase is transparently documented as deferred with no false empirical claim.
- [ ] Any Kaggle traces use a same-tokenizer model pair and include full provenance.
- [ ] Hugging Face Dataset contains only sanitized artifacts and a clear dataset card.
- [ ] Hugging Face Space is a precomputed replay lab, not a fragile live-serving demo.
- [ ] Public case study and walkthrough contain evidence boundaries and non-claims.

### 28.7 Final maturity claim

The strongest allowable final maturity statement is:

> **Research-grade, production-shaped policy evaluation harness. Locally validated with deterministic synthetic trace replay and, if completed, supplemental small-model Kaggle evidence. Not a production serving engine, not live-traffic validated, and not a DSpark reproduction.**

---


## 28.8 Post-V4 route reconciliation

ADR-0017 records the project-level decision after V4 closeout.

The reconciliation distinguishes the reusable implementation foundation from the unproven
north-star claim:

```text
implemented foundation
  -> causal contracts and guard
  -> synthetic trace and manifest discipline
  -> fixed and threshold baselines
  -> isolated unsafe control
  -> deterministic per-case replay
  -> descriptive baseline evidence ledger
  -> calibration and held-out assessment controls

missing core proof
  -> fresh eligible calibration path
  -> causal load-aware adaptive scheduler
  -> declared capacity-profile implementation
  -> shared utility scorer and comparison report
  -> valid same-input adaptive-versus-baseline evidence
```

ADR-0018 constitutes V5 as the bounded successor programme. It fixes one globally shared
bounded monotone-beta calibration method, fresh evidence namespaces, complete held-out gate
semantics, a conservative fallback, and a hard stop decision before V5 evidence exists.

The next V5 implementation slice must build typed artifact and assessment contracts plus a
non-final complete-gate regression harness. It must not author V5 calibration or final-evaluation
evidence, fit a V5 artifact, or implement a scheduler. V5 remains a pre-fixture route until that
contract boundary is merged.

## 29. Change-control rules

Any change to the following requires an ADR or explicit PRD amendment:

- absolute north star;
- causal information boundary;
- evidence hierarchy;
- core policy comparison set;
- split policy;
- public-data policy;
- scope ceiling;
- final claim boundary;
- project phase exit gates.

Any change to trace fields, policy configuration, calibration method, or capacity profile must be versioned and recorded in the relevant manifest/report.

No future implementation slice may redefine success after observing final evaluation results without documenting the change and rerunning the governed evaluation process.

---

## 30. Reference basis

This PRD is grounded in the project’s current repository constitution and causal-information contracts, plus the DSpark paper’s central engineering lessons:

- parallel draft generation can suffer suffix-quality decline;
- confidence used for scheduling must be calibrated;
- verification budget should account for system capacity;
- retrospective future-token-dependent decisions can violate non-anticipation and invalidate lossless claims;
- apparent throughput or utility gains are insufficient without correctness constraints.

Primary paper reference:

> Xin Cheng et al. (2026). *DSpark: Confidence-Scheduled Speculative Decoding with Semi-Autoregressive Generation.*

---

## 31. Final governing statement

SpecSafe succeeds only when it can demonstrate all of the following together:

1. **The policy uses lawful decision-time information.**
2. **The confidence driving the policy is evaluated for calibration.**
3. **The policy is compared against blunt baselines on identical immutable evidence.**
4. **The system identifies conditions where adaptive scheduling does not win.**
5. **The public artifact states exactly what it proves and does not prove.**

Anything less is a scheduling demo.

SpecSafe is intended to be a disciplined reliability artifact.
