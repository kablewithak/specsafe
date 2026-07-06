# ADR-0013: Retain the V3 Final Assessment as Non-Authorizing Evidence

- **Status:** Accepted
- **Date:** 2026-07-06
- **Decision owner:** Kabo Molefe
- **Applies from:** `main` after PR #56 (`1cb6a55`)
- **Depends on:** ADR-0010, ADR-0011, ADR-0012, and the committed V3 final held-out calibration assessment

## Context

ADR-0010 fixed the V3 calibration-fitness gate before V3 final evidence existed. That gate required all of the following before a probability-driven adaptive-policy claim could proceed:

1. locked final-manifest integrity;
2. at least 96 final observations;
3. calibrated Brier improvement of at least `0.005`;
4. calibrated 10-bin expected calibration error improvement of at least `0.010`;
5. calibrated AUROC no more than `0.001` below raw AUROC;
6. at least 20 final observations at each candidate position;
7. byte-identical assessment rebuild determinism.

PR #56 committed a write-once V3 final held-out calibration result. It retained these direct results:

```text
assessment cases=24
assessment observations=96
raw Brier score=0.18762604166666666
calibrated Brier score=0.13631510416666667
Brier improvement=0.05131093749999999

raw 10-bin ECE=0.2665625
calibrated 10-bin ECE=0.1583333333333333
10-bin ECE improvement=0.10822916666666668

status=passes_held_out_fitness
runtime_control_eligible=false
scheduler_or_policy_execution_performed=false
write_mode=write_once
```

The retained V3 result proves that, under its committed implementation, the frozen quantile-isotonic transform improved the recorded Brier and 10-bin ECE metrics across the frozen 24-case / 96-observation corpus.

A post-merge reconciliation found a material mismatch between the accepted V3 gate and the implemented PR #56 assessment:

- the committed V3 assessment protocol used `0.0` as both minimum improvement thresholds instead of ADR-0010's `0.005` Brier and `0.010` ECE thresholds;
- the assessment did not calculate or retain raw and calibrated AUROC;
- the assessment therefore did not enforce ADR-0010's AUROC ranking-safety requirement;
- the assessment did not retain a byte-identical rebuild proof for the committed final result;
- the assessment test module correctly avoided scoring the frozen final fixtures, but therefore did not prove the complete ADR-0010 final-gate behavior on the final corpus.

The numerical Brier and ECE improvements exceed ADR-0010's stated numeric floors. That fact does not remove the missing AUROC and final-output determinism evidence.

## Decision

Retain the committed PR #56 `result.json` as immutable, non-authorizing V3 calibration diagnostic evidence.

Do not reinterpret its `passes_held_out_fitness` status as satisfying the complete ADR-0010 V3 calibration-fitness gate.

The V3 programme is not authorised to begin any of the following from this result:

- `causal-marginal-prefix-v1` implementation;
- V3 fixed-baseline execution against final evidence;
- V3 policy-comparison execution;
- V3 threshold or capacity-policy tuning;
- a V3 adaptive-policy advantage, conditional-advantage, or runtime-control claim;
- a replacement or overwrite of the committed V3 final assessment.

The committed `result.json`, frozen final-evaluation manifest, final-evidence index, calibration manifest, calibration artifact, and calibration fit report remain unchanged.

## Why no corrective rerun is allowed

The final V3 corpus has already been consumed by the committed one-time assessment. Adding AUROC or a revised gate implementation now and executing it against the same final cases would create a second post-hoc final assessment after the first held-out result is known.

That would weaken split discipline rather than repair it.

The project must not:

- delete the existing result;
- overwrite the existing result;
- create a second V3 final-assessment result;
- change the V3 calibrator using final evidence;
- tune a V3 policy against final outcomes;
- claim that the missing AUROC condition is satisfied by inference.

## Consequences

### Evidence retained

The project may truthfully state:

> The frozen V3 quantile-isotonic calibration artifact improved Brier score by `0.0513109375` and 10-bin expected calibration error by `0.1082291667` on the retained V3 final corpus under the committed PR #56 assessment implementation.

This is synthetic held-out calibration diagnostic evidence only.

### Claims blocked

The project may not state:

- that the complete ADR-0010 V3 calibration-fitness gate passed;
- that V3 calibration is fit for an adaptive scheduler under the original constitution;
- that any V3 policy improves utility against the predeclared baselines;
- that a scheduler is authorised;
- any runtime-control, production-serving, latency, throughput, or cost claim.

### Next programme decision

A future V4 programme may be proposed only with:

1. a fresh calibration corpus;
2. a fresh final-evaluation corpus;
3. a fully predeclared held-out assessment protocol that includes Brier, ECE, AUROC, position coverage, deterministic-result verification, and final report fields;
4. unit tests for every gate;
5. no reuse of V3 final-evaluation outcomes for method selection, threshold selection, fixture authoring, or policy tuning.

V4 is not automatically authorised by this ADR. It requires its own charter and evidence constitution before new data or policy code is written.

## Reproduction references

```text
assessment result:
evidence/heldout-calibration/v3-final-heldout-calibration-assessment-v1/result.json

assessment implementation:
src/specsafe/heldout_calibration/v3_final_assessment.py

assessment tool:
tools/run_v3_final_heldout_calibration_assessment.py

assessment unit tests:
tests/test_v3_final_heldout_calibration_assessment.py

governing V3 method and gate:
docs/adr/ADR-0010-v3-method-and-evidence-constitution.md
```

## Final control statement

V3 produced useful calibration diagnostics. It did not produce a fully constitution-compliant final calibration gate.

The honest next step is to preserve that fact, stop V3 policy promotion, and use the failure to strengthen the next fresh evidence programme rather than retrofit a positive claim onto already-observed held-out evidence.
