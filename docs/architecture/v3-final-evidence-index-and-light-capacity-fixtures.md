# V3 Final Evidence Index and Light-Capacity Fixtures

## Purpose

This slice begins V3 held-out evidence authoring without altering the frozen calibration registry, calibration manifest, quantile-isotonic artifact, or fit report.

## Separate provenance paths

```text
frozen calibration registry
→ frozen calibration manifest
→ frozen quantile-isotonic artifact

separate final_evidence_index.json
→ final_evaluation/ runtime and outcome case pairs
→ future final-evaluation manifest
```

The separate index pins SHA-256 hashes for the four frozen calibration assets. It reserves all 24 final cases but authorises only the six light-capacity pairs in this slice.

## Authored light-capacity family

- Case IDs: `CRV3-201` through `CRV3-206`
- Split: `final_evaluation`
- Data role: `held_out_evaluation`
- Capacity profile ID: `synthetic-v3-final-light-capacity`
- Workload balance: two `structured_text`, two `code`, two `open_ended_chat` cases
- Request pressure: one or two active requests

Runtime inputs contain lawful pre-sample confidence, visible-prefix state, and capacity snapshots only. Candidate tokens and outcomes remain in separate post-hoc files.

## Explicit limits

This slice does not create a final-evaluation manifest, score, calibration assessment, scheduler, capacity policy, promotion decision, or runtime-control claim. The fitted calibrator must not run against partial final evidence.

## Next boundary

The next authorised authoring slice may add only `CRV3-207` through `CRV3-212` for moderate capacity.
