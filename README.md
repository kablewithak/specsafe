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

The PRD is the governing product and experiment contract. When sources conflict, it takes precedence over ADRs, committed implementation evidence, session notes, and earlier discussion.

## Delivery status

| Milestone | Status | Evidence boundary |
|---|---|---|
| Repository and project constitution | Complete | Repository identity, package scaffold, and project scope exist. |
| Causal-information boundary | Complete | Strict runtime contract and deterministic rejection of retrospective contexts. |
| PRD adoption | Complete | Governing research and experiment contract is committed. |
| Synthetic trace fixture foundation | Complete | Versioned runtime inputs, separate expected outcomes, manifests, and deterministic fixture validation are committed. |
| Synthetic policy baselines | In progress | Fixed-length, static-threshold, and unsafe retrospective controls are being added behind the causal boundary. |
| Calibration and confidence fitness | Blocked | Requires completed Phase 2 baseline evidence. |
| Causal load-aware scheduling | Blocked | Requires held-out calibration and fitness evidence. |
| Replay evaluation and reports | Blocked | Requires the valid adaptive policy and declared scoring contract. |
| Kaggle evidence and public replay release | Blocked | Amplifies, but does not replace, the local evidence harness. |

## Current maturity

**Contracts enforced; Phase 2 synthetic evidence foundation in progress.** The repository contains strict runtime contracts, a deterministic causal-safety gate, versioned synthetic fixture assets, and their associated integrity checks. The branch currently under review adds the blunt policy controls needed for Phase 2.

No calibrated policy, adaptive policy, policy-utility result, replay comparison, Kaggle model experiment, public replay demo, throughput result, losslessness result, or production-readiness claim exists yet.

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
