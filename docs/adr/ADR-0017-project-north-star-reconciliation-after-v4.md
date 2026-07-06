# ADR-0017: Reconcile SpecSafe’s North Star After V4 Closeout

- **Status:** Accepted
- **Date:** 2026-07-07
- **Decision owner:** Kabo Molefe
- **Applies from:** `main` after V4 closeout at commit `5c3fd8b`
- **Depends on:** `docs/PRD.md`, ADR-0001, ADR-0002, ADR-0009, ADR-0014, ADR-0015, ADR-0016
- **Supersedes:** No prior ADR. It reconciles programme status; it does not alter historical evidence.

## Context

SpecSafe’s north star remains:

> Build a reproducible lab that proves whether an LLM verification scheduler can spend limited
> compute more intelligently than blunt fixed rules, without using forbidden future information
> or breaking its correctness guarantee.

V4 is closed by ADR-0016 as a valid immutable held-out calibration result with
`RANKING_SAFETY_REGRESSION`. V4 improved Brier score and ECE but degraded AUROC beyond its
predeclared ranking-safety budget. It therefore cannot authorize V4 scheduler work, policy
comparison, runtime control, refit, threshold tuning, rerun, or remediation in place.

A post-V4 repository audit at `main` commit `5c3fd8b` establishes that the repository is further
along than the historical phase labels in the PRD and earlier programme handovers suggested.
The audit found implemented source and test seams for:

```text
src/specsafe/contracts/
src/specsafe/causal_safety/
src/specsafe/traces/
src/specsafe/scheduling/
src/specsafe/trace_replay/
src/specsafe/evidence_ledger/
src/specsafe/calibration/
src/specsafe/confidence_fitness/
src/specsafe/heldout_calibration/
src/specsafe/metrics/
```

The audit also establishes that several north-star components remain absent:

```text
src/specsafe/capacity_profiles/     # absent
src/specsafe/eval_harness/          # absent
src/specsafe/reporting/             # absent
causal load-aware adaptive policy   # absent
shared policy-utility scorer        # absent
valid cross-policy comparison report # absent
Kaggle notebook / measured profile  # absent
Hugging Face proof assets           # absent
```

## Audit findings

### Reusable foundation that is implemented

| Boundary | Audited evidence | Status |
|---|---|---|
| Causal runtime contract | `CausalSchedulerContext`, exact-type guard, strict output contracts, unsafe retrospective context | Complete |
| Synthetic trace governance | Versioned runtime inputs, separate expected outcomes, manifests, provenance validation, multiple historical fixture roots | Complete |
| Valid blunt baselines | `FixedLengthVerificationPolicy` and `StaticThresholdVerificationPolicy` | Complete |
| Unsafe negative control | `UnsafeRetrospectiveLookaheadPolicy` and isolated retrospective replay path | Complete and non-promotable |
| Deterministic replay | `run_valid_policy_replay()` retains decisions before labels and excludes causal-fail decisions | Complete per case |
| Baseline evidence retention | `BaselineReplayEvidenceLedger` covers fixed and threshold policies on development and adversarial splits | Complete but deliberately non-comparative |
| Calibration controls | Raw-confidence diagnostics, frozen calibration contracts, held-out assessment contracts, ranking metric utility | Complete as calibration/evidence infrastructure |
| V4 result | One write-once final held-out calibration result, closed by ADR-0016 | Complete negative evidence |

### Missing proof components

| North-star requirement | Current position | Why it matters |
|---|---|---|
| Causal load-aware adaptive policy | Not implemented | There is no intervention that uses calibrated confidence and current capacity together. |
| Capacity-profile implementation | Not implemented | `CapacitySnapshot` exists, but there is no versioned profile package or declared marginal-capacity model. |
| Shared policy-utility scoring | Not implemented | Per-case replay summaries exist, but no common utility function combines accepted work, waste, and capacity cost. |
| Valid adaptive-versus-baseline comparison | Not implemented | The baseline ledger is intentionally descriptive and carries `no_cross_policy_winner_claim`. |
| Comparison reporting | Not implemented | No machine-readable comparison result or human-readable comparison report exists. |
| Kaggle and public proof | Not started | These are downstream evidence amplification, not replacements for the local core proof. |

## Decision

### 1. Reclassify the current project position

SpecSafe has completed the **Phase 2 foundation** required for later policy comparison:

```text
synthetic traces
+ valid fixed and threshold baselines
+ isolated unsafe control
+ deterministic per-case replay
+ descriptive baseline evidence ledger
```

This status does not mean the core thesis is proven. The project is accurately described as:

```text
contracts enforced
+ synthetic-fixture validated
+ held-out calibration assessed as a retained negative result
- not held-out replay evaluated
- not Kaggle-environment evaluated
- not public replay demo released
- not production-serving validated
```

### 2. Preserve V4 as historical evidence, not an implementation route

V4 remains closed under ADR-0016. No V4 source, fixture, manifest, result, policy comparison,
capacity policy, or runtime-control work is authorized by this ADR.

V4 final inputs, final outcomes, calibration artifact parameters, and final result metrics are not
successor-programme tuning inputs. The only transferable inputs are project-process lessons:

- use one immutable final assessment;
- keep calibration and ranking criteria independent;
- retain exact provenance and write-once results;
- fail closed before a policy receives confidence-driven control authority.

### 3. Separate the project’s proof path into two explicit gates

```text
Gate A — fresh calibration eligibility
  A new method-and-evidence constitution
  -> fresh calibration evidence
  -> fresh final evidence
  -> complete held-out calibration and ranking gate
  -> either eligible for controlled adaptive-policy research or closed negative

Gate B — core policy proof
  eligible causal adaptive policy
  + declared capacity profiles
  + fixed and threshold baselines
  + same immutable replay inputs
  + shared scorer
  + causal validity
  -> valid adaptive-versus-baseline comparison report
```

Gate A is necessary but not sufficient. Gate B is the north-star proof boundary.

### 4. Authorize only a fresh, bounded successor constitution next

The next implementation slice may be documentation-only and must create a successor constitution
before any new data, calibrator, scheduler, or replay comparison is authored.

The successor constitution must:

1. create a new fixture root and case namespace;
2. choose either one fixed calibration method or a finite selection procedure using calibration
   evidence only;
3. define a complete final gate with probability-quality, ranking-safety, coverage, provenance,
   no-refit, and write-once criteria;
4. define a conservative fallback;
5. define the exact condition under which the successor closes permanently rather than starting
   another unbounded calibration revision;
6. state the pre-existing baseline/replay assets it will reuse without changing;
7. prohibit use of V4 final bytes, labels, outcomes, artifact parameters, or final metrics for
   successor tuning;
8. not implement an adaptive scheduler, capacity profile, utility scorer, or comparison report yet.

### 5. Do not start another calibration programme merely to continue activity

A successor programme is justified only because a passing calibration eligibility gate is required
before the adaptive-policy proof can begin. It must be bounded by an explicit stop rule.

The successor must not claim that calibration quality alone answers the north-star question. A
calibration pass only permits controlled policy research; it does not establish utility,
throughput, latency, cost, or production value.

## Alternatives considered

| Alternative | Decision | Reason |
|---|---|---|
| Patch or rerun V4 | Rejected | V4 final evidence is consumed and ADR-0016 prohibits remediation in place. |
| Treat Phase 2 as unimplemented and rebuild baselines/replay | Rejected | Audited source and tests already implement the required foundation. |
| Build the adaptive scheduler immediately | Rejected | No eligible calibrated confidence path exists after V4’s failed final gate. |
| Build Kaggle or a public UI next | Rejected | Neither substitutes for the local same-input policy-comparison proof. |
| Start an open-ended V5 calibration search | Rejected | It would repeat a post-hoc iteration pattern and weaken evidence discipline. |
| Create a bounded fresh successor constitution | Accepted | It preserves V4 integrity while creating the only lawful route to Gate B. |

## Consequences

### Positive

- The repository’s progress is described accurately: the baseline/replay foundation is reusable,
  while the core adaptive-policy proof remains incomplete.
- The next work avoids needless rewrites of fixed baselines and deterministic replay.
- Calibration remains a gate, not a substitute for a policy result.
- The successor is constrained by a stop rule rather than open-ended method chasing.
- Kaggle and public-release work remain correctly sequenced after the local core proof.

### Costs

- The project cannot yet claim an adaptive-policy advantage.
- The next material evidence programme must use fresh data and a fresh final split.
- A successor may still close negative, leaving the project as a credible reliability foundation
  rather than a completed policy-performance proof.

## Claims after this ADR

### Permitted

- SpecSafe has a causal, synthetic baseline, replay, and evidence-retention foundation.
- Fixed-length and static-threshold policies can be replayed causally on immutable synthetic cases.
- The baseline ledger is descriptive and does not claim a cross-policy winner.
- V4 is a retained negative held-out calibration result that blocks V4 policy work.
- The project’s next missing core component is not another baseline; it is an eligible
  calibration path followed by a causal adaptive-policy comparison.

### Forbidden

- A causal adaptive scheduler exists.
- A capacity-aware policy has been evaluated.
- A valid adaptive-versus-baseline comparison has run.
- Verification waste, throughput, latency, or cost improved.
- Kaggle or public replay evidence exists.
- V4 can be repaired or used for policy selection.
- The project is held-out replay evaluated, production ready, or a DSpark reproduction.

## Acceptance criteria

This decision is complete only when:

- `docs/PRD.md` uses reconciled phase and maturity wording;
- `README.md` uses reconciled delivery status and does not imply an adaptive scheduler exists;
- the repository retains this ADR;
- no V4 evidence bytes, result bytes, manifests, or source files are changed;
- no new calibration fixture, final-evaluation fixture, scheduler, capacity profile, utility scorer,
  or policy-comparison code is added;
- `main` is clean after merge.

## Final control statement

> SpecSafe has enough foundation to stop rebuilding its baseline layer. Its remaining proof path is
> explicit: a bounded fresh calibration eligibility programme first, then a causally valid,
> capacity-aware, same-input policy comparison. Until both gates are satisfied, the project is a
> credible reliability and evaluation harness, not a completed policy-performance result.
