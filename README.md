# SpecSafe

**SpecSafe: Causal Confidence-Scheduled Verification Policy Lab** is a research-grade
policy-evaluation lab for testing whether confidence-calibrated, load-aware LLM verification
policies can reduce low-value verification work without violating explicit causal correctness
constraints.

It is inspired by scheduling and non-anticipation concerns in speculative-decoding research. It
is **not** a DSpark reproduction, a production LLM serving engine, or evidence of live-traffic
throughput improvement.

## North star

> Build a reproducible lab that proves whether an LLM verification scheduler can spend limited
> compute more intelligently than blunt fixed rules, without using forbidden future information
> or breaking its correctness guarantee.

## What exists

SpecSafe contains:

- strict typed trace, confidence, capacity, scheduling, and report contracts;
- deterministic causal-safety validation and an isolated retrospective unsafe control;
- immutable synthetic runtime inputs with physically separate post-hoc outcomes;
- fixed-length and static-threshold causal baselines;
- governed synthetic calibration, capacity profiles, utility scoring, and matched replay;
- a research-only causal load-aware policy with conservative fallback;
- a controlled synthetic adaptive-versus-baseline comparison and Phase 5 report;
- governed Kaggle Qwen trace collection, retained archives, diagnostics, and provenance;
- a retained Kaggle-derived candidate calibrator and fit-pool replay;
- an independent no-refit holdout replay;
- a formal promotion closeout that rejected the candidate after a ranking-safety regression;
- a public, hash-verified Hugging Face bounded negative-evidence Dataset;
- a frozen read-only Hugging Face Space evidence contract;
- a public five-file static Hugging Face Space with no live inference or input collection;
- retained Dataset and Space publication receipts;
- anonymous Space repository, file-hash, revision, and application reconciliation; and
- a final PRD acceptance review, case study, walkthrough, and closeout runbook.

SpecSafe does not contain in v1:

- a DSpark reimplementation or trained DSpark drafter;
- custom CUDA kernels or a production serving engine;
- a promoted Kaggle-derived calibrator, threshold, or scheduler;
- live-traffic or production-throughput evidence;
- private prompts, client data, secrets, or raw sensitive model payloads in public artifacts.

## Architecture

```text
strict contracts
  -> causal-safety boundary
  -> versioned traces and manifests
  -> calibration and confidence-fitness gates
  -> capacity profiles
  -> fixed, threshold, adaptive, fallback, and unsafe policies
  -> deterministic matched replay
  -> evaluation and failure taxonomy
  -> machine-readable and Markdown reports
  -> frozen public evidence
  -> static Dataset and Space release receipts
  -> anonymous reconciliation
```

| Boundary | Purpose |
|---|---|
| `src/specsafe/contracts/` | Strict Pydantic contracts, enums, typed results, and validation errors. |
| `src/specsafe/causal_safety/` | Reject future-bearing or retrospective runtime information. |
| `src/specsafe/calibration/` | Fit, assess, and close confidence candidates under declared gates. |
| `src/specsafe/capacity_profiles/` | Retain versioned light, moderate, saturated, jagged, and measured evidence classes. |
| `src/specsafe/scheduling/` | Implement valid baselines, causal adaptive policy, fallback, and unsafe control. |
| `src/specsafe/trace_replay/` | Run deterministic same-input policy replay. |
| `src/specsafe/eval_harness/` | Score outcomes, classify failures, and enforce regression gates. |
| `src/specsafe/reporting/` | Produce evidence-bounded machine-readable and human-readable reports. |
| `apps/specsafe-reliability-lab/` | Render the frozen read-only public evidence surface. |
| `evidence/publication-receipts/` | Retain immutable Dataset and Space release evidence. |

## Governing documents

- [Product Requirements Document](docs/PRD.md)
- [Final PRD acceptance review](docs/experiments/specsafe-final-acceptance-review.md)
- [Final closeout runbook](docs/runbooks/specsafe-final-closeout.md)
- [Project constitution](docs/PROJECT_CONSTITUTION.md)
- [Architecture decisions](docs/adr/)
- [Controlled synthetic Phase 5 report](docs/reports/v5-controlled-synthetic-policy-comparison.md)
- [Candidate-calibrator promotion closeout](docs/adr/ADR-0042-close-candidate-calibrator-promotion.md)
- [Bounded negative-evidence publication route](docs/adr/ADR-0043-bounded-negative-evidence-publication-route.md)
- [Space publication receipt decision](docs/adr/ADR-0054-retain-and-reconcile-space-publication-receipt.md)
- [Final case study](docs/case-studies/specsafe-final-case-study.md)
- [One-minute walkthrough](docs/walkthroughs/specsafe-one-minute-walkthrough.md)

Public proof:

- [Hugging Face Dataset](https://huggingface.co/datasets/KaboKableMolefe/specsafe-bounded-negative-evidence-v1)
- [Hugging Face Space repository](https://huggingface.co/spaces/KaboKableMolefe/specsafe-reliability-lab)
- [Hugging Face Space application](https://kabokablemolefe-specsafe-reliability-lab.static.hf.space)

The PRD remains the governing product and experiment contract. The final acceptance review updates
repository facts and phase status without weakening the PRD's causal, evidence, privacy, or
publication requirements.

## Delivery status

| Milestone | Status | Evidence boundary |
|---|---|---|
| Repository and project constitution | Complete | Repository identity, package scaffold, scope ceiling, and governing documents are retained. |
| Causal-information boundary | Complete | Runtime policy inputs exclude retrospective and future-derived information. |
| Synthetic trace and baseline foundation | Complete | Versioned fixtures, fixed policies, unsafe control, and deterministic replay are retained. |
| Synthetic calibration and confidence fitness | Complete for V5 | The bounded monotone-beta calibrator passed its frozen synthetic held-out gate. |
| Synthetic causal load-aware policy | Complete for controlled research | The policy is causally guarded, capacity-aware, and supports conservative fallback. |
| Controlled synthetic policy comparison | Complete | Same-input adaptive-versus-baseline evidence and a Phase 5 gate are retained. |
| Kaggle small-model evidence | Complete for the current candidate path | Qwen traces, fit evidence, independent holdout replay, and closeout evidence are retained. |
| Kaggle candidate-calibrator promotion | Closed, not promoted | Brier and fixed-bin ECE improved, but ranking safety regressed beyond tolerance. |
| Threshold and scheduler promotion from Kaggle evidence | Not authorized | The current candidate is unfit for probability-driven automation. |
| Bounded public negative-evidence pack | Published and verified | The exact nine-file Dataset is public, ungated, hash-verified, and tied to a retained publication receipt. |
| Hugging Face Space | Published and anonymously reconciled | The exact five-file static Space is public, read-only, hash-verified, and requires no provider-side build. |
| Final PRD acceptance and closeout | Complete | Requirements, evidence boundaries, final maturity, case study, walkthrough, and non-mutating closeout gate are retained. |
| Production validation | Out of scope | No live serving, operational load, production latency, throughput, cost, or customer-data evidence exists. |

## Current maturity

**Research-grade, production-shaped policy evaluation harness; deterministic synthetic replay
validated; Kaggle environment evaluated; failed confidence candidate retained as diagnostic
negative evidence; public Dataset and read-only Space released and reconciled.**

The controlled synthetic harness demonstrates reproducible causal policy comparison under declared
fixtures and capacity profiles. The Kaggle evidence layer demonstrates a stronger reliability
behavior: a candidate that improved aggregate Brier score and fixed-bin ECE was still rejected
because its independent holdout AUROC degradation breached the predeclared ranking-safety limit.

```text
highest_confirmed_evidence_level=public_replay_demo_released
candidate=v5-qwen-combined-fixed-bin-isotonic-calibrator-v1
decision=KEEP_DIAGNOSTIC_ONLY
promotion_attempt_status=closed_not_promoted
automated_scheduling_confidence_status=unfit_use_conservative_fallback
public_dataset_status=published_anonymously_verified
public_space_status=published_anonymously_reconciled
production_serving_validated=false
```

This is not a production-readiness claim. The current candidate may not drive automated scheduling,
threshold promotion, scheduler promotion, or adaptive-policy utility claims.

## Controlled result

```text
adaptive_vs_fixed=2_wins_3_neutral_1_loss
adaptive_vs_threshold=3_wins_2_neutral_1_loss
adaptive_loss=MPC5-103
clearest_adaptive_wins=MPC5-104_MPC5-105
```

The supported conclusion is bounded: adaptive scheduling helped under some controlled conditions,
was neutral under others, and lost in one. No global superiority claim is supported.

## Project status

SpecSafe v1 engineering is closed at the public replay demo boundary.

A successor calibrator is not an automatic next step. Any successor requires a separate
predeclared method-and-evidence charter, fresh fit evidence, and fresh independent promotion
evidence. The consumed holdout may not be reused for fitting, threshold tuning, scheduler tuning,
or repeated method selection.

Any live-serving, customer-data, production-load, or new remote-publication route requires a new
scope decision and evidence plan. Optional portfolio packaging may continue without changing the
retained research outcome.

## Local development

Python requires version 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

The local Space shell uses Node 20.19 or newer and npm 10 or newer.

```powershell
Push-Location .\apps\specsafe-reliability-lab
npm ci
npm run check
Pop-Location
```

See [the local visual-shell runbook](docs/runbooks/hugging-face-space-local-visual-shell.md) for
browser smoke tests and the manual visual-review gate. See the
[Space receipt-verification runbook](docs/runbooks/hugging-face-space-publication-receipt-verification.md)
for the retained publication and reconciliation boundary.

## License

The bounded negative-evidence Dataset is published under CC BY 4.0 for the exact sanitized
publication materials. That license does not apply to the SpecSafe source repository as a whole,
retained archives, raw traces, the calibrator artifact, or upstream model materials.
