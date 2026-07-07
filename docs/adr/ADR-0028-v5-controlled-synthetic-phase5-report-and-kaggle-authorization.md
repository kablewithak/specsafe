# ADR-0028: Close Local Controlled Synthetic Phase 5 and Authorize Kaggle Evidence Acquisition

## Status

Accepted.

## Context

SpecSafe has retained one canonical governed comparison result for the frozen six-case
controlled synthetic corpus. The result includes identical-input comparisons among fixed-length,
static-threshold, and calibrated causal load-aware policies, plus an unsafe retrospective control
that is retained separately as causal-fail evidence.

The remaining local-core task is to turn that retained evidence into a deterministic report and
apply a bounded Phase 5 gate. The report must preserve all outcomes, including adaptive-policy
losses and neutral cases. It must not rerun the governed result, refit calibration, choose a global
winner, promote runtime control, or expand claims beyond controlled synthetic evidence.

## Decision

Add a deterministic reporting and Phase 5 gate boundary that:

- verifies the exact retained result SHA-256;
- validates the result through its strict contract;
- requires six valid matched comparisons and six unsafe-control exclusions;
- requires higher, neutral, and lower adaptive-policy outcomes against each valid baseline;
- renders a canonical Markdown report from the retained result only;
- retains a canonical machine-readable gate artifact; and
- authorizes the separately labelled Kaggle evidence-acquisition phase only.

The Phase 5 gate shall set:

```text
validity_marker=VALID_COMPARISON
evidence_class=synthetic_controlled
evidence_maturity_label=synthetic_fixture_validated
phase5_gate_status=passes_controlled_synthetic_phase5_gate
kaggle_experiment_authorized=true
public_replay_release_authorized=false
runtime_control_eligible=false
promotion_eligible=false
```

## Consequences

### Enables

- a deterministic human-readable report tied to retained machine-readable evidence;
- a bounded statement that the controlled synthetic comparison preserved mixed outcomes and
  excluded unsafe causal controls;
- Phase 6 Kaggle notebook and trace-collection planning;
- a clear handoff from local fixture proof to separately labelled environment-specific evidence.

### Does not enable

- final held-out policy evaluation;
- a global policy winner or threshold tuning;
- runtime policy control or promotion;
- public replay release;
- throughput, latency, cost-saving, serving-capacity, live-traffic, or production claims.

## Failure posture

The reporting gate fails when:

- the retained comparison result hash drifts;
- the strict result contract no longer validates;
- final-evaluation access or calibration refit is recorded;
- an unsafe control is no longer causal-fail and excluded;
- the six-case coverage changes;
- any higher, neutral, or lower outcome category is removed;
- the committed gate or report does not match deterministic derivation.

## Follow-on boundary

Phase 6 may begin with a Kaggle experiment design and same-tokenizer model-pair selection gate.
Kaggle remains an environment-specific evidence-acquisition layer; it does not change the current
maturity label or authorize public release.
