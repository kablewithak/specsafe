# ADR-0040: Govern Kaggle Negative-Case Expansion Before Calibration Fit

## Status

Proposed for adoption.

## Context

The retained `v5-qwen-governed-trace-collection-v2 / attempt-001-t4` archive expanded the Kaggle evidence layer from the earlier small trace sample to 120 runtime records and 120 expected-outcome records.

The v2 calibration diagnostic is directionally supportive but does not authorize calibration fitting:

```text
observed_record_count=120
observed_positive_count=97
observed_negative_count=23
minimum_record_count_for_calibration_fit=100
minimum_positive_count_for_calibration_fit=30
minimum_negative_count_for_calibration_fit=30
calibration_fit_authorized=false
readiness_status=insufficient_negative_count_for_calibration_fit_signal_supportive
```

The current blocker is not total sample count. It is negative-class coverage. The archive has enough records and positives, but it is short by seven negative examples under the declared minimum. Calibration fitting, threshold promotion, scheduler promotion, public release, and production claims therefore remain blocked.

A naive response would be to fit anyway, lower the negative minimum, or select thresholds from diagnostic replay. Those options weaken the evidence boundary and create avoidable leakage risk. The next safe move is to govern a targeted negative-case expansion before collecting additional Kaggle traces.

## Decision

Adopt a governed negative-case expansion programme before any Kaggle-derived calibration fit.

The expansion will be a third Kaggle collection boundary, tentatively identified as:

```text
collection_id=v5-qwen-governed-negative-case-expansion-v1
attempt_id=attempt-001-t4
```

The purpose is to increase nonmatch/negative-class coverage for calibration-readiness diagnostics while preserving the existing causal, split, and evidence boundaries.

The expansion may use self-authored high-entropy prompts, ambiguous continuations, adversarially worded but safe continuations, and open-ended prompt families that are more likely to expose draft/target divergence. The expansion must not use customer data, private prompts, secrets, private source code, personally identifying information, or sensitive raw payloads.

## Required controls

1. The expansion corpus must be self-authored and public-safe.
2. Prompt families must be assigned before model execution.
3. Prompt/task-level split discipline must be preserved.
4. Runtime-visible fields must remain separated from expected-outcome labels.
5. The expansion must not tune thresholds or fit calibration in Kaggle.
6. The expansion must not redefine the calibration-readiness gate after observing outcomes.
7. The expansion must retain a pre-collection manifest before any model execution.
8. The expansion must retain archive artifacts with deterministic local tests before analysis.
9. The combined diagnostic must explicitly state whether it uses v2 only, expansion only, or v2 plus expansion.
10. Calibration fitting remains blocked until a separate diagnostic gate authorizes it.

## Minimum target

The immediate target is not a balanced dataset for production modelling. It is enough additional negative coverage to support the declared readiness minimum.

Recommended target:

```text
planned_prompt_count=16
planned_candidate_positions_per_prompt=4
planned_runtime_records=64
minimum_additional_negative_target=12
minimum_combined_negative_target=30
```

The `minimum_additional_negative_target` is a planning target, not a guarantee. The model outcome distribution is unknown before execution. If the third archive still does not reach the readiness threshold, the project must preserve that result as evidence rather than silently weakening the gate.

## Options considered

### Option A: Fit a calibrator using v2 only

Rejected.

v2 passes total count and positive count, but the diagnostic gate says negative count is insufficient. Fitting anyway would make the gate decorative rather than governing.

### Option B: Lower the negative threshold from 30 to 23

Rejected for now.

Changing the readiness minimum immediately after seeing the result creates avoidable post-hoc governance risk. Any future threshold change would require an explicit ADR/PRD-compatible justification and rerun of diagnostics.

### Option C: Combine v1 and v2 immediately

Deferred.

A combined diagnostic may be useful, but v1 and v2 differ in corpus size and collection boundary. The next safer step is to govern the negative expansion first, then decide whether combined analysis is appropriate.

### Option D: Govern targeted negative-case expansion

Accepted.

This preserves evidence discipline while addressing the actual blocker: insufficient negative examples for calibration fitting.

## Consequences

What becomes easier:

- Calibration-readiness diagnostics can reach the declared negative minimum without weakening the gate.
- The project gains a more robust failure/nonmatch sample for calibration analysis.
- Public proof later becomes more credible because weak/failure cases are intentionally retained.

What becomes harder:

- A third Kaggle run may be required.
- Prompt authoring must be careful not to become outcome cherry-picking.
- The combined-evidence story must be documented cleanly.

## Non-claims

This ADR does not authorize:

- Kaggle-derived calibration fitting;
- threshold tuning or promotion;
- scheduler promotion;
- public dataset release;
- Hugging Face Space release;
- production speedup, latency, throughput, cost, or readiness claims.

## Next safe implementation slice

After this ADR merges, the next safe slice is authoring the negative-case expansion prompt corpus and manifest tests. No model execution should occur until that corpus and pre-collection manifest are retained.
