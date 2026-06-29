# SpecSafe

**SpecSafe: Causal Confidence-Scheduled Verification Policy Lab** is a research-grade policy-evaluation lab for testing whether confidence-calibrated, load-aware LLM verification policies can reduce low-value verification work without violating explicit causal correctness constraints.

It is inspired by scheduling and non-anticipation concerns in speculative-decoding research. It is **not** a DSpark reproduction, a production LLM serving engine, or evidence of live-traffic throughput improvement.

## North star

> Build a reproducible lab that proves whether an LLM verification scheduler can spend limited compute more intelligently than blunt fixed rules, without using forbidden future information or breaking its correctness guarantee.

## What this repository will contain

- typed trace, confidence, capacity, and scheduling contracts;
- fixed-policy, static-threshold, and causal load-aware scheduling baselines;
- confidence calibration and held-out evaluation;
- causal-safety regression fixtures and negative controls;
- synthetic trace replay plus optional small-model Kaggle evidence;
- machine-readable results and buyer-readable reports;
- a Hugging Face replay demo that uses sanitized, precomputed traces.

## What this repository will not contain in v1

- a DSpark reimplementation or trained DSpark drafter;
- custom CUDA kernels or a production serving engine;
- live-traffic or production-throughput claims;
- private prompts, client data, secrets, or raw model payloads in public artifacts.

## Governing documents

- [Product Requirements Document](docs/PRD.md)
- [Project constitution](docs/PROJECT_CONSTITUTION.md)
- [Architecture decisions](docs/adr/)
- [Synthetic trace fixture contract](docs/architecture/synthetic-trace-fixture-contract.md)
- [Synthetic policy baselines](docs/architecture/synthetic-policy-baselines.md)
- [Deterministic synthetic policy replay](docs/architecture/deterministic-synthetic-policy-replay.md)
- [Baseline replay evidence ledger](docs/architecture/baseline-replay-evidence-ledger.md)
- [Calibration split and raw-confidence fitness](docs/architecture/calibration-split-and-confidence-fitness.md)
- [Frozen calibrator contract](docs/architecture/frozen-calibrator-contract.md)
- [Held-out calibration fitness and promotion gate](docs/architecture/heldout-calibration-fitness.md)

The PRD is the governing product and experiment contract. When sources conflict, it takes precedence over ADRs, committed implementation evidence, session notes, and earlier discussion.

## Delivery status

| Milestone | Status | Evidence boundary |
|---|---|---|
| Repository and project constitution | Complete | Repository identity, package scaffold, and project scope exist. |
| Causal-information boundary | Complete | Strict runtime contract and deterministic rejection of retrospective contexts. |
| PRD adoption | Complete | Governing research and experiment contract is committed. |
| Synthetic trace fixture foundation | Complete | Versioned runtime inputs, separate expected outcomes, manifests, and deterministic fixture validation are committed. |
| Synthetic policy baselines | Complete | Fixed-length and static-threshold baselines plus an isolated unsafe retrospective control are committed. |
| Deterministic synthetic policy replay | Complete | Typed sequential replay retains decisions before post-hoc labels and separates valid from causally invalid replay results. |
| Baseline replay evidence ledger | Complete | Typed descriptive ledger covers fixed and threshold baseline replay on development and adversarial cases only; it carries no winner claim. |
| Calibration split and raw-confidence fitness | Complete | Two calibration-only fixtures and a predeclared diagnostic protocol are versioned and tested. |
| Frozen calibrator contract | Complete | A calibration-only histogram artifact is typed, deterministic, and blocked from runtime control pending held-out assessment. |
| Held-out calibration fitness and promotion gate | Complete — negative result | Final evaluation retains raw-versus-calibrated metrics; the current frozen calibrator regresses and is not promoted. |
| Causal load-aware scheduling | Blocked | Requires a new governed calibration approach that clears held-out fitness without final-evaluation tuning. |
| Replay evaluation and reports | Blocked | Requires a valid adaptive policy and declared scoring contract. |
| Kaggle evidence and public replay release | Blocked | Amplifies, but does not replace, the local evidence harness. |

## Current maturity

**Contracts enforced; calibration evidence closed on a reproducible negative result.** The repository contains strict causal runtime contracts, immutable synthetic fixture assets, deterministic baseline policies, sequential replay records, a descriptive baseline ledger with no-winner posture, calibration-only diagnostics, a frozen histogram calibrator, and a final-evaluation report that blocks promotion after the current calibrator regresses on held-out fitness.

No adaptive policy, policy-utility result, cross-policy winner, Kaggle model experiment, public replay demo, throughput result, losslessness result, or production-readiness claim exists yet.

## Local development

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check src tests
```

## License

A license will be selected before the first public artifact release.
