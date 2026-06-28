# SpecSafe Project Constitution

## Purpose

SpecSafe is a standalone research-grade side project. It evaluates verification-budget policies for speculative-decoding-style traces under explicit calibration, capacity, and causal-correctness constraints.

## Absolute north star

> Build a reproducible lab that proves whether an LLM verification scheduler can spend limited compute more intelligently than blunt fixed rules, without using forbidden future information or breaking its correctness guarantee.

## Primary research question

> Under controlled trace-replay conditions, does a calibrated, causal, load-aware verification policy improve defined policy utility relative to fixed-length and static-threshold baselines?

## Core invariants

1. A valid scheduler may use only information available at the moment each verification decision is made.
2. An apparent utility gain is rejected when it depends on forbidden future information.
3. Calibration and final evaluation data must remain separated at the prompt/task level.
4. Every policy comparison must run against identical immutable traces and capacity profiles.
5. Public artifacts may not contain client data, secrets, private prompts, raw model payloads, or unnecessary sensitive text.

## Scope ceiling

SpecSafe v1 is a policy and evaluation harness. It does not include a production serving engine, custom kernels, DSpark training, live traffic, or production-speed claims.

## Evidence posture

- Synthetic fixtures establish deterministic causal and policy behavior.
- Optional Kaggle experiments provide small-model evidence only.
- Hugging Face hosts a replay interface backed by sanitized precomputed artifacts.
- All reports must distinguish synthetic, Kaggle-measured, and unproven production evidence.

## Release rule

No public performance or correctness claim may exceed the strongest directly reproducible evidence retained in this repository.
