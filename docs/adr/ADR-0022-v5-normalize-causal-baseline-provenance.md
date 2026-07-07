# ADR-0022: Normalize Causal Baseline Provenance Before Policy Comparison

- **Status:** accepted
- **Date:** 2026-07-07
- **Decision owner:** SpecSafe project
- **Applies to:** fixed-length and static-threshold verification baselines

## Context

ADR-0021 added governed synthetic capacity profiles. SpecSafe already has two valid
baselines: a fixed verification-length rule and a static confidence-threshold rule. Both
are intentionally capacity-blind. They are useful comparison controls only if later
matched replay can retain exactly which immutable policy configuration produced each
result.

The existing baseline replay ledger retained policy configuration objects but did not yet
standardize a cross-policy descriptor with a configuration hash, classification, and
capacity-sensitivity declaration. This left future comparison work able to infer baseline
identity from implementation-specific objects instead of an explicit contract.

## Decision

Add a normalized `BaselinePolicyDescriptor` for the currently authorized valid baselines.
Every descriptor records:

- stable `policy_id`;
- `policy_kind` (`fixed_length` or `static_threshold`);
- `classification=valid_baseline`;
- `capacity_sensitivity=capacity_blind`;
- SHA-256 hash of the exact immutable configuration.

The fixed-length and static-threshold policies expose this descriptor through a read-only
`descriptor` property. The existing development/adversarial baseline evidence ledger now
retains the descriptor alongside its typed configuration and rejects any mismatch.

## Consequences

### Positive

- Later same-input comparison work can retain policy configuration identity deterministically.
- Baselines remain explicitly capacity-blind rather than silently acquiring adaptive logic.
- The ledger can reject descriptor/configuration drift before an evidence artifact is kept.
- The current slice does not alter V5 frozen calibration evidence, final fixtures, replay
  scoring, or scheduler behavior.

### Deliberately not included

- No adaptive policy.
- No utility scorer.
- No valid policy-comparison report.
- No capacity-profile evaluation inside a baseline decision.
- No change to static-threshold values or fixed-length budgets.
- No throughput, latency, cost, or policy-winner claim.

## Verification

Regression coverage must prove:

1. fixed and static-threshold descriptors carry valid-baseline and capacity-blind labels;
2. configuration hashes are deterministic and content-sensitive;
3. baseline actions remain unchanged when only capacity snapshot values differ;
4. ledger descriptors match their retained typed configuration exactly;
5. strict contracts reject winner or other unapproved comparison fields.

## Evidence boundary

This ADR improves policy provenance only. It does not establish that any policy is
load-aware, useful, superior to another policy, or representative of production serving.
