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

## Repository scope

SpecSafe contains and will extend:

- typed trace, confidence, capacity, and scheduling contracts;
- strict causal-safety validation and an isolated unsafe retrospective control;
- versioned synthetic trace fixtures with separate runtime inputs and post-hoc outcomes;
- fixed-length and static-threshold causal baselines;
- deterministic synthetic policy replay and descriptive baseline evidence ledgers;
- governed calibration and held-out assessment protocols;
- future causal load-aware scheduling, capacity profiles, policy comparison, reports, optional
  small-model Kaggle evidence, and a public replay demonstration only when their gates permit.

SpecSafe does not contain in v1:

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
- [Post-V4 north-star reconciliation](docs/adr/ADR-0017-project-north-star-reconciliation-after-v4.md)
- [V5 bounded calibration eligibility charter](docs/adr/ADR-0018-v5-bounded-monotone-beta-calibration-eligibility-charter.md)

The PRD is the governing product and experiment contract. When sources conflict, it takes
precedence over ADRs, committed implementation evidence, session notes, and earlier discussion.

## Delivery status

| Milestone | Status | Evidence boundary |
|---|---|---|
| Repository and project constitution | Complete | Repository identity, package scaffold, and project scope exist. |
| Causal-information boundary | Complete | Strict runtime contract and deterministic rejection of retrospective contexts. |
| PRD adoption and post-V4 reconciliation | Complete | Governing contract is adopted and reconciled against audited repository state. |
| Synthetic trace fixture foundation | Complete | Versioned runtime inputs, separate expected outcomes, manifests, and deterministic fixture validation are committed. |
| Synthetic policy baselines | Complete | Fixed-length and static-threshold baselines plus an isolated unsafe retrospective control are committed. |
| Deterministic synthetic policy replay | Complete | Typed sequential replay retains decisions before post-hoc labels and separates valid from causally invalid replay results. |
| Baseline replay evidence ledger | Complete | Typed descriptive ledger covers fixed and threshold baseline replay on development and adversarial cases only; it carries no winner claim. |
| Calibration programmes | V1–V4 historical; V5 chartered pre-fixture | V4 remains immutable negative evidence. ADR-0018 fixes V5’s fresh namespace, bounded monotone-beta method, complete held-out gate, and hard stop rule before any V5 data exists. |
| Causal load-aware scheduler | Not implemented | No causal adaptive scheduler has been evidenced in source. |
| Capacity profiles and shared policy utility | Not implemented | Capacity exists only as typed snapshot/fixture metadata; no standalone profile package or shared scorer exists. |
| Valid cross-policy comparison and reports | Not implemented | No adaptive-versus-baseline comparison on identical frozen inputs has been retained. |
| Kaggle evidence and public replay release | Not started | These amplify, but do not replace, the local evidence harness. |

## Current maturity

**Contracts enforced; synthetic-fixture validated; held-out calibration assessed as a retained
negative result.**

The repository has a reusable causal and replay foundation, but it has not reached
`held-out replay evaluated`. V4 is closed: it must not be refit, tuned, rerun, used for V4 policy
comparison, or treated as a runtime-control candidate.

No causal adaptive-policy result, cross-policy winner claim, Kaggle model experiment, public
replay demo, throughput result, losslessness result, or production-readiness claim exists yet.

## Next governed route

V5 is chartered but has no fixtures, fitted artifact, final result, scheduler, or policy claim.

```text
V5 typed artifact and final-assessment contracts
  -> non-final complete-gate regression harness
  -> V5 calibration fixtures and frozen calibration artifact
  -> V5 final fixtures and one write-once held-out eligibility assessment
  -> capacity, causal adaptive-policy, shared-score, and comparison contracts only if V5 passes
  -> supplemental Kaggle evidence
  -> public replay proof
```

The project must not start V5 fixture authoring before its typed contract and non-final gate tests
exist. It must not start a V4 remediation or immediate scheduler slice.

## Local development

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check src tests
python -m ruff format --check .
```

## License

A license will be selected before the first public artifact release.
