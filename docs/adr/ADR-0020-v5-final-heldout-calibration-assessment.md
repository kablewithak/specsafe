# ADR-0020: V5 Frozen Held-Out Calibration Assessment

- **Status:** Accepted and executed
- **Date:** 2026-07-07
- **Decision:** Assess the retained V5 bounded-monotone-beta calibrator exactly once against the frozen final-evaluation corpus.

## Context

V5 calibration evidence was frozen before fitting. The V5 final-evaluation corpus was authored independently, then frozen into a manifest and label-free evidence index before assessment. The next permitted operation was one write-once held-out calibration assessment.

## Decision

The assessment loads only:

- `calibration_manifest.json`;
- `bounded_monotone_beta_calibration_artifact.json`;
- `bounded_monotone_beta_calibration_fit_diagnostics.json`;
- `final_evaluation_manifest.json`;
- `final_evidence_index.json`;
- the manifest-named final runtime inputs and separate expected outcomes.

It does not refit the calibrator, select a threshold, run a scheduler, compare policies, replay a runtime policy, or authorize runtime control.

The retained result is written once at:

```text
evidence/heldout-calibration/v5-final-heldout-calibration-assessment-v1/result.json
```

The registry transitions only after that file has been written and canonically validated.

heldout_result_sha256=f985ef8df30a5d920194a05f7d5115431420f8ed40a1252d33af62f5d0882ab9

## Result

```text
status=PASSES_V5_CALIBRATION_ELIGIBILITY_GATE
case_count=36
observation_count=144
raw_brier=0.30406180555555556
calibrated_brier=0.26017302217016014
brier_improvement=0.043888783385395425
raw_ece_10_bin=0.23131944444444447
calibrated_ece_10_bin=0.12478925813015543
ece_10_bin_improvement=0.10653018631428904
raw_auroc=0.5034965034965035
calibrated_auroc=0.5034965034965035
auroc_delta=0.0
```

All coverage, provenance, monotonicity, Brier, ECE, ranking-safety, no-refit, no-policy-execution, write-once, and canonical-serialization gate checks passed.

## Consequences

V5 is eligible for controlled causal load-aware policy research. This is not a policy comparison result, production claim, scheduler authorization, or runtime-control authorization. The next artefact must establish controlled policy foundations: capacity profiles, shared utility semantics, valid baselines, and causal adaptive decision contracts.
