# V5 Kaggle Negative-Case Expansion Readiness Checklist

Use this checklist before authoring or running the negative-case expansion.

## Current blocker

```text
calibration_fit_authorized=false
reason=insufficient_negative_count_for_calibration_fit_signal_supportive
observed_negative_count=23
minimum_negative_count_for_calibration_fit=30
```

## Corpus authoring checklist

- [ ] Corpus is self-authored.
- [ ] Corpus contains no PII, secrets, private prompts, customer data, or private source code.
- [ ] Corpus has 16 prompts.
- [ ] Each prompt has four planned candidate positions.
- [ ] Planned record count is 64.
- [ ] Prompt families are assigned before model execution.
- [ ] Related prompt variants do not cross split boundaries.
- [ ] No expected outcome labels are authored before model execution.
- [ ] No calibration parameters are introduced.
- [ ] No thresholds are promoted.

## Pre-collection checklist

- [ ] Manifest records source corpus hash.
- [ ] Manifest records prompt count and planned runtime record count.
- [ ] Manifest records model pair identity.
- [ ] Manifest records `model_execution_status=not_started`.
- [ ] Manifest records `calibration_fit_status=not_authorized`.
- [ ] Manifest records `threshold_promotion_status=not_authorized`.
- [ ] Manifest records `scheduler_promotion_status=not_authorized`.
- [ ] Manifest records `production_claim_status=not_authorized`.
- [ ] Manifest is retained before model execution.

## Kaggle run checklist

- [ ] Dataset remains private during collection.
- [ ] Notebook records exact model IDs and revisions.
- [ ] Notebook records tokenizer ID and revision.
- [ ] Notebook records package versions and hardware metadata.
- [ ] Notebook records seed and decoding configuration.
- [ ] Notebook does not print secrets.
- [ ] Notebook does not fit calibration.
- [ ] Notebook does not tune or promote thresholds.
- [ ] Notebook exports sanitized runtime/outcome records.
- [ ] Notebook writes a retention manifest and archive ZIP.

## Post-collection checklist

- [ ] Archive is uploaded back to the local repo workflow.
- [ ] Archive retention PR lands before analysis.
- [ ] Local analysis reads retained artifacts only.
- [ ] Local replay remains diagnostic only.
- [ ] Calibration diagnostic explicitly states whether fitting is authorized.
- [ ] If negative count remains insufficient, calibration remains blocked.

## Forbidden shortcuts

Do not:

- lower the negative-count gate just because v2 has 23 negatives;
- combine archives without declaring the evidence boundary;
- fit calibration in Kaggle;
- select thresholds from replay diagnostics;
- claim production speedup or serving readiness;
- publish artifacts before public-safety review.
