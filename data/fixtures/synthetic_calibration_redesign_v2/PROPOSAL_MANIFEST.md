# V2 Registry Finalization Bundle Manifest

## Purpose

This bundle adds a deterministic finalization path from the reviewed V2 registry proposal to a hash-linked
`scenario_family_registry.json` generated locally from the committed proposal. It also adds typed in-memory
V2 case contracts. It is not a runtime fixture manifest.

## Delivered files and generated output

```text
data/fixtures/synthetic_calibration_redesign_v2/scenario_family_registry_proposal.json  existing retained provenance
data/fixtures/synthetic_calibration_redesign_v2/scenario_family_registry.json           generated locally
data/fixtures/synthetic_calibration_redesign_v2/authoring_ledger.md
src/specsafe/traces/calibration_redesign_v2.py
src/specsafe/traces/calibration_redesign_v2_cases.py
tools/finalize_calibration_redesign_v2_registry.py
tests/test_calibration_redesign_v2.py
tests/test_calibration_redesign_v2_cases.py
docs/architecture/calibration-redesign-v2-registry-finalization-and-case-contracts.md
```

## Finalization controls

1. The builder accepts the proposal-only root and writes one finalized registry.
2. The finalized registry stores the SHA-256 of the exact committed proposal bytes.
3. Family IDs, case IDs, split roles, source-template fingerprints, rationale, failure modes, and quarantine
   flags must match the reviewed proposal exactly when the finalized registry is loaded.
4. V2 runtime-input assets, expected-outcome assets, and both manifests remain prohibited.
5. V1 data-bearing namespaces remain prohibited as V2 inputs, test expectations, or provenance sources.

## Case-contract controls

1. Runtime inputs are strict and contain no candidate token IDs or observed labels.
2. Expected outcomes are strict, post-hoc, and structurally separate from runtime inputs.
3. Every future V2 case requires at least four aligned observation positions.
4. Replay alignment requires visible prefixes to match prior post-hoc candidate token IDs.
5. Registry membership requires a finalized V2 registry and one reserved V2 case ID.

## Non-claims

This bundle does not create a V2 fixture, fit bounded Platt scaling, assess V2 calibration, or authorize
adaptive scheduling.
