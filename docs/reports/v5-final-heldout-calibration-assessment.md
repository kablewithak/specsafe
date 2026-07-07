# V5 Final Held-Out Calibration Assessment

## Validity marker

```text
PASSES_V5_CALIBRATION_ELIGIBILITY_GATE
```

## Evidence

```text
calibration_manifest=ed950e222462a57575c4b644bc5cfd57a763a99150a83a90ab207c9bc20d7aed
calibration_artifact=a3baeb2db94221d68a69fc757c8865e384e3ac92ca05585919188fe1c744cd14
calibration_fit_diagnostics=3f697caa5e621351a786ce043c931e6a84e3255f6108a6b9a64c77840dbc0971
final_evaluation_manifest=5887a63cfa7e185fb93c6d0a346946dea53c79051f5c9010da012e5ce4e2ac36
final_evidence_index=0be444e275916efe21381998a67f1f4b960e619dfd9957bdedd5ee2ad56a8b2a
```

heldout_result_sha256=f985ef8df30a5d920194a05f7d5115431420f8ed40a1252d33af62f5d0882ab9

## Aggregate metrics

| Metric | Raw | Calibrated | Delta / improvement |
|---|---:|---:|---:|
| Brier score | 0.30406180555555556 | 0.26017302217016014 | +0.043888783385395425 |
| ECE, 10 bins | 0.23131944444444447 | 0.12478925813015543 | +0.10653018631428904 |
| Tie-aware AUROC | 0.5034965034965035 | 0.5034965034965035 | 0.0 |

## Gate outcome

All predeclared checks passed:

- frozen manifest and provenance alignment;
- 36 case pairs and 144 observations;
- 36 observations at each candidate position;
- 48 observations for each workload type;
- retained monotonicity verification;
- minimum Brier and ECE improvement;
- no AUROC degradation beyond the permitted bound;
- no calibration refit, scheduler, policy execution, or threshold selection;
- canonical write-once serialization.

## Interpretation

The frozen V5 calibrator improves probability reliability on this synthetic held-out corpus while preserving ranking exactly. It is therefore eligible only for controlled policy research.

## Boundary

This report does not demonstrate that an adaptive scheduler beats fixed or threshold baselines. It does not establish capacity benefit, serving speed, live traffic behavior, or runtime-control readiness.
