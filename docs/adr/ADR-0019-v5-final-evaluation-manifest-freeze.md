# ADR-0019: Freeze the V5 Final-Evaluation Manifest Before Assessment

- **Status:** Accepted
- **Date:** 2026-07-07
- **Decision:** Freeze the complete V5 held-out corpus as a write-once final-evaluation manifest and a label-free final-evidence index before any V5 held-out assessment is executed.

## Context

V5 calibration evidence was frozen before the bounded monotone-beta method was fitted. The complete held-out corpus now exists independently under `final_evaluation/`:

```text
CSV5-201..CSV5-236
36 case pairs
72 source assets
144 observations
```

The final corpus covers curve coverage, position spread, workload variation, and mixed-reliability contrast. Without a final manifest, future assessment code could accidentally evaluate a changed held-out corpus or silently mix evidence states.

## Decision

The project writes two immutable root-level evidence artifacts:

```text
final_evaluation_manifest.json
final_evidence_index.json
```

The manifest records every final runtime-input and expected-outcome asset, case pair, scenario family, byte count, SHA-256, aggregate SHA-256, and the pre-freeze registry SHA-256.

The final-evidence index records only label-free case inventory metadata: case ID, trace ID, workload type, family, and paired file paths. It does not expose post-hoc acceptance labels or candidate token IDs.

The registry advances to `final_evaluation_manifest_frozen` and carries the manifest hash, index hash, and pre-freeze registry hash. The next authorised artifact becomes the single governed V5 held-out calibration assessment.

## Consequences

- The V5 held-out corpus is immutable for assessment purposes.
- Calibration evidence and the retained fit remain unchanged.
- The final manifest is not an assessment result.
- No threshold selection, refit, scheduler, capacity-profile, utility-score, baseline comparison, policy replay, or runtime-control path is introduced.
- Any changed held-out asset, manifest, index, or registry provenance hash blocks trustworthy loading.

## Rejected alternatives

1. **Assess directly from final case directories.** Rejected because the exact held-out inventory would not be independently frozen.
2. **Create only a manifest.** Rejected because the assessment protocol needs a label-free case inventory reference for auditability.
3. **Freeze and assess in one change.** Rejected because an immutable final evidence boundary must exist before the assessment reads it.
