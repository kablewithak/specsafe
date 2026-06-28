# SpecSafe

**SpecSafe** is a research-grade lab for evaluating whether confidence-calibrated, load-aware LLM verification policies can reduce low-value verification work without violating explicit causal correctness constraints.

It is inspired by the scheduling and non-anticipation concerns in speculative decoding research. It is **not** a reproduction of DSpark, a production LLM serving engine, or a claim of live-traffic throughput improvement.

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

## Project phases

1. Repository and project constitution
2. Contracts and causal boundary
3. Synthetic traces and policy baselines
4. Calibration and confidence fitness
5. Causal load-aware scheduling
6. Evaluation and negative controls
7. Kaggle small-model evidence
8. Public proof release and PRD reconciliation

The core proof boundary is complete after the policy harness, calibration, causal-safety suite, and fixed trace-replay evaluation are complete. Kaggle and Hugging Face amplify evidence; they do not replace the core proof.

## Local development

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

## Current maturity

**Phase 1 — typed causal-information boundary.** The project now has strict runtime contracts
for visible-prefix decisions and a deterministic gate that rejects retrospective contexts carrying
future sampled-token or verification-outcome information. No scheduler, model experiment,
performance result, or production-readiness claim exists yet.

## License

A license will be selected before the first public artifact release.
