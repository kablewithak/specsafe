# ADR-0012: Keep V3 Final-Evaluation Evidence in a Separate Index

- **Status:** Accepted
- **Date:** 2026-07-05
- **Decision owner:** Kabo Molefe

## Context

The frozen V3 calibration manifest records the exact SHA-256 hash and byte count of `scenario_family_registry.json`. Changing that registry after calibration freeze would make the frozen calibration manifest fail integrity verification, even if all calibration case bytes remained unchanged.

V3 final-evaluation case authoring must therefore not mutate the calibration registry, calibration manifest, fitted quantile-isotonic artifact, or fit report.

## Decision

Create a separate final-evidence index for V3 held-out case authoring. The index is a new artifact with its own schema, hash, and explicit authoring status. It references only the reserved V3 final family identifiers, case ranges, workload allocation, and isolation rules. It is not part of the calibration manifest.

The existing `scenario_family_registry.json` remains frozen as calibration provenance. It continues to reserve the full V3 inventory but is never rewritten during final-evidence authoring.

## Consequences

- Calibration manifest integrity remains stable after final cases are authored.
- The quantile-isotonic artifact and fit report remain reproducible from the frozen calibration corpus.
- Final-evaluation authoring has a separate, inspectable provenance boundary.
- A later final-evaluation manifest can hash the final evidence and the separate final-evidence index without modifying calibration evidence.

## Non-goals

This ADR does not author final case bytes, score hidden cases, fit another calibrator, add capacity-profile code, implement a scheduler, or make a performance claim.
