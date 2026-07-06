# V3 Final Jagged-Capacity Fixtures

## Purpose

This slice completes authoring of the separate V3 held-out final-evidence inventory. It adds the jagged-capacity family while keeping the frozen calibration registry, calibration manifest, quantile-isotonic artifact, and fit report unchanged.

## Authored jagged-capacity family

- Case IDs: `CRV3-219` through `CRV3-224`
- Split: `final_evaluation`
- Data role: `held_out_evaluation`
- Capacity profile ID: `synthetic-v3-final-jagged-capacity`
- Workload balance: two `structured_text`, two `code`, and two `open_ended_chat` cases
- Capacity shape: non-monotonic current active-request counts and verification-batch demand across each four-position trace

Runtime inputs contain lawful pre-sample confidence, visible-prefix state, and current capacity snapshots only. Candidate tokens, observed-acceptance labels, and prefix-survival labels remain in separate post-hoc outcome files.

## Complete pre-manifest corpus

```text
final cases authored: 24 of 24
final observations authored: 96 of 96
final-evaluation manifest: absent
held-out assessment: absent
scheduler and policy code: absent
adversarial-regression evidence: absent
```

## Preserved calibration path

```text
frozen calibration registry
→ frozen calibration manifest
→ frozen quantile-isotonic artifact
→ frozen fit report

separate final_evidence_index.json
→ all 24 held-out final-evaluation case pairs
→ next: complete final-evaluation manifest freeze
→ only then: one-time held-out assessment
```

## Explicit limits

This slice does not create the final-evaluation manifest, score final evidence, run a held-out calibration assessment, run the fitted calibrator against held-out evidence, add a scheduler, create a capacity policy, make a promotion decision, or author adversarial cases.

## Next boundary

The next authorised slice may freeze `final_evaluation_manifest.json` over all 24 held-out runtime/outcome case pairs. It must leave frozen calibration assets unchanged and must not run the one-time held-out assessment.

After the manifest is merged, stop for the formal handover before any held-out scoring occurs.
