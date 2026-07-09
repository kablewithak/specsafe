# Kaggle Trace Corpus Expansion V1 — Authoring Ledger

## Status

`planned_pre_collection_not_model_evidence`

This ledger records the self-authored prompt-family corpus for the second governed Kaggle trace collection. It is an authoring and planning artifact only. It does not contain model outputs, target labels, calibration parameters, threshold choices, or scheduler utility claims.

## Files

| Path | Role |
|---|---|
| `data/fixtures/kaggle_trace_corpus_expansion_v1/prompt_corpus.json` | Planned self-authored prompt-family corpus |
| `data/fixtures/kaggle_trace_corpus_expansion_v1/manifest.json` | Corpus manifest and hash lock |

## Corpus hash

```text
prompt_corpus_sha256=bc6dee060c4da77796f8c45c3a131bd49d9198432f9588c95096aaefdd0a8466
```

## Authoring rules applied

- All prompts are self-authored and public-safe.
- No client data, private prompts, private documents, private source code, credentials, secrets, or personal data are included.
- Splits are assigned at prompt-family level.
- Final-evaluation prompt families are isolated from development and calibration prompt families.
- Each prompt plans four candidate positions, giving 120 planned runtime records before model execution.
- Positive and negative counts are not claimed before model execution.

## Workload balance

| Workload | Prompt families | Planned records |
|---|---:|---:|
| structured_text | 10 | 40 |
| code | 10 | 40 |
| open_ended_chat | 10 | 40 |

## Split balance

| Split | Prompt families | Planned records | Role |
|---|---:|---:|---|
| development | 9 | 36 | Notebook/debug plumbing only |
| calibration | 9 | 36 | Candidate calibration split for a later authorized fit only if diagnostics pass |
| final_evaluation | 9 | 36 | Final scoring only after collection and freeze |
| adversarial_regression | 3 | 12 | Regression prompts for leakage and non-anticipation checks |

## Forbidden actions

Do not use this corpus to:

- fit a Kaggle-derived calibrator before a retained second archive exists;
- tune or promote thresholds;
- promote a scheduler utility result;
- publish a public dataset without a public-safety review;
- claim production speedup, live-serving throughput, cost savings, or production readiness.

## Next gate

The next safe gate after this slice is notebook/pre-collection wiring that reads this corpus, preserves split metadata, and emits a pre-collection manifest. It must still avoid calibration fitting and threshold promotion.
