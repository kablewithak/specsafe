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

SpecSafe now contains:

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
- a formal promotion closeout that rejected the candidate after a ranking-safety regression.

SpecSafe does not contain in v1:

- a DSpark reimplementation or trained DSpark drafter;
- custom CUDA kernels or a production serving engine;
- a promoted Kaggle-derived calibrator, threshold, or scheduler;
- live-traffic or production-throughput evidence;
- private prompts, client data, secrets, or raw sensitive model payloads in public artifacts.

## Governing documents

- [Product Requirements Document](docs/PRD.md)
- [Current PRD status reconciliation](docs/PRD_STATUS_RECONCILIATION_2026-07-10.md)
- [Project constitution](docs/PROJECT_CONSTITUTION.md)
- [Architecture decisions](docs/adr/)
- [Controlled synthetic Phase 5 report](docs/reports/v5-controlled-synthetic-policy-comparison.md)
- [Candidate-calibrator promotion closeout](docs/adr/ADR-0042-close-candidate-calibrator-promotion.md)
- [Bounded negative-evidence publication route](docs/adr/ADR-0043-bounded-negative-evidence-publication-route.md)

The PRD remains the governing product and experiment contract. The dated status reconciliation
updates repository facts and phase status without weakening the PRD's causal, evidence, privacy,
or publication requirements.

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
| Bounded public negative-evidence pack | Next | Local deterministic packaging only; actual publication remains a later explicit gate. |
| Hugging Face Dataset and Space publication | Not started | Requires a sanitized pack, license decision, publication review, and explicit evidence labels. |
| Production validation | Out of scope | No live serving, operational load, production latency, throughput, or cost evidence exists. |

## Current maturity

**Controlled synthetic policy comparison complete; Kaggle environment evaluated; current Kaggle
candidate closed as diagnostic negative evidence.**

The controlled synthetic harness demonstrates reproducible causal policy comparison under declared
fixtures and capacity profiles. The Kaggle evidence layer demonstrates a stronger reliability
behavior: a candidate that improved aggregate Brier score and fixed-bin ECE was still rejected
because its independent holdout AUROC degradation breached the predeclared ranking-safety limit.

```text
candidate=v5-qwen-combined-fixed-bin-isotonic-calibrator-v1
decision=KEEP_DIAGNOSTIC_ONLY
promotion_attempt_status=closed_not_promoted
automated_scheduling_confidence_status=unfit_use_conservative_fallback
public_release_status=bounded_negative_evidence_only
```

This is not a production-readiness claim. The current candidate may not drive automated scheduling,
threshold promotion, scheduler promotion, or adaptive-policy utility claims.

## Next governed route

```text
post-closeout repository reconciliation
  -> deterministic bounded negative-evidence release pack
  -> publication-readiness review and license decision
  -> optional Hugging Face Dataset / CPU-only precomputed replay surface
  -> final project reconciliation and handover
```

A new calibrator is not an automatic next step. Any successor requires a separate predeclared
method-and-evidence charter, fresh fit evidence, and fresh independent promotion evidence. The
consumed holdout may not be reused for fitting, threshold tuning, scheduler tuning, or repeated
method selection.

## Local development

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

## License

A license must be selected before the first public artifact is published. The local bounded
negative-evidence pack may be prepared before that decision, but publication remains blocked.
