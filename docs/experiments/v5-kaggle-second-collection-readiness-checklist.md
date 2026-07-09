# V5 Kaggle Second Collection Readiness Checklist

Use this checklist before authoring, running, or retaining the second governed Kaggle trace collection.

## 1. Repo and evidence state

- [ ] `main` is clean before the collection-prep branch starts.
- [ ] Latest retained first archive remains unchanged.
- [ ] Existing trace analysis, replay, and calibration diagnostic reports are not edited as part of corpus planning.
- [ ] No stale report hashes are reused without verification.

## 2. Corpus authoring controls

- [ ] Every prompt family has a stable ID.
- [ ] Every prompt family declares workload type.
- [ ] Every prompt family declares intended confidence regime.
- [ ] Every prompt family declares split role before model outcome observation.
- [ ] Related variants are kept in the same split role.
- [ ] No prompt is selected or removed after reviewing target outcomes unless the removal reason is safety, duplication, or schema invalidity and is documented.

## 3. Public-safety controls

- [ ] No PII.
- [ ] No secrets.
- [ ] No credentials.
- [ ] No private prompts.
- [ ] No client data.
- [ ] No private source code.
- [ ] No sensitive logs.
- [ ] No raw customer artifacts.
- [ ] No API keys, cookies, tokens, `.env` values, or local credential paths.

## 4. Collection configuration controls

- [ ] Target model ID and revision are recorded.
- [ ] Draft model ID and revision are recorded.
- [ ] Tokenizer ID and revision are recorded.
- [ ] Same-tokenizer assumption is verified or inherited from a retained preflight gate.
- [ ] Decode configuration is recorded.
- [ ] Seed is recorded.
- [ ] Kaggle hardware/runtime metadata is recorded.
- [ ] Package versions are recorded.
- [ ] Notebook/script revision is recorded.

## 5. Runtime/outcome separation

- [ ] Runtime-visible records exclude target-derived labels.
- [ ] Expected outcome records contain target-derived labels only for post-hoc diagnostics.
- [ ] Runtime policy code does not read expected outcome labels.
- [ ] Threshold replay remains diagnostic only.
- [ ] Calibration fitting remains blocked until a later authorization gate.

## 6. Minimum diagnostic targets

- [ ] Planned runtime record target is at least 100.
- [ ] Planned expected outcome record target is at least 100.
- [ ] Class-balance readiness target is at least 30 positives.
- [ ] Class-balance readiness target is at least 30 negatives.
- [ ] Contingency prompt families exist if class balance is weak.
- [ ] Contingency use is documented before any fit decision.

## 7. Retention outputs

- [ ] Trace archive ZIP is retained intentionally.
- [ ] Retention manifest is written.
- [ ] Trace summary is written.
- [ ] Artifact hashes are written.
- [ ] Known limitations are written.
- [ ] Collection notes state that this is Kaggle-environment evidence, not production-serving evidence.

## 8. Local post-collection gates

- [ ] Archive validation passes.
- [ ] Trace analysis report is generated deterministically.
- [ ] Diagnostic replay report is generated deterministically.
- [ ] Calibration diagnostic report is generated deterministically.
- [ ] Readiness status is explicit.
- [ ] If readiness fails, the failure is retained as evidence instead of hidden.

## 9. Forbidden work in this checklist boundary

- [ ] Do not fit a Kaggle-derived calibrator.
- [ ] Do not tune or promote thresholds.
- [ ] Do not promote a scheduler from Kaggle traces.
- [ ] Do not publish a Hugging Face Dataset.
- [ ] Do not publish a Hugging Face Space.
- [ ] Do not claim production speedup, latency, throughput, cost savings, or production readiness.

## 10. Exit condition

This checklist is satisfied only when corpus authoring, public-safety review, split discipline, collection configuration, runtime/outcome separation, and retention requirements are all confirmed before the second governed collection run is treated as evidence-bearing.
