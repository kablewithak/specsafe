# V3 Final Saturated-Capacity Fixtures

## Purpose

This slice extends the separate V3 held-out final-evidence inventory with the saturated-capacity family while keeping the frozen calibration registry, calibration manifest, quantile-isotonic artifact, and fit report unchanged.

## Authored saturated-capacity family

- Case IDs: `CRV3-213` through `CRV3-218`
- Split: `final_evaluation`
- Data role: `held_out_evaluation`
- Capacity profile ID: `synthetic-v3-final-saturated-capacity`
- Workload balance: two `structured_text`, two `code`, and two `open_ended_chat` cases
- Request pressure: eight, nine, or ten active requests
- Verification batch tokens: six through nine across the four candidate positions

Runtime inputs contain lawful pre-sample confidence, visible-prefix state, and capacity snapshots only. Candidate tokens, observed-acceptance labels, and prefix-survival labels remain in separate post-hoc outcome files.

## Preserved calibration path

```text
frozen calibration registry
→ frozen calibration manifest
→ frozen quantile-isotonic artifact
→ frozen fit report

separate final_evidence_index.json
→ authored light, moderate, and saturated held-out case pairs
→ future complete final-evaluation manifest
```

The index now records eighteen authored held-out case pairs. It still reserves the jagged family without authoring its bytes.

## Explicit limits

This slice does not create a final-evaluation manifest, score final evidence, run a held-out calibration assessment, run the fitted calibrator against held-out evidence, add a scheduler, create a capacity policy, make a promotion decision, or author adversarial cases.

## Next boundary

The next authorised authoring slice may add only `CRV3-219` through `CRV3-224` for jagged capacity. It must extend the separate final-evaluation subtree and index only, leaving frozen calibration assets unchanged.
