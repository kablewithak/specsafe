# ADR-0011: Gate V3 Final-Evaluation Evidence Authoring

- **Status:** Accepted
- **Date:** 2026-07-05
- **Decision scope:** V3 final-evaluation evidence only

## Context

V3 calibration evidence is frozen in `calibration_manifest.json`, and the predeclared `quantile-isotonic-calibration-v1` artifact has been fitted from that frozen calibration corpus.

The project may now create fresh V3 final-evaluation evidence. This evidence is the only evidence permitted to decide whether V3 confidence calibration holds on unseen cases and, later, whether a causal capacity-aware policy is eligible for evaluation.

The final-evaluation corpus must not be shaped by V1 or V2 held-out outcomes, V3 calibration outcomes, the fitted V3 artifact values, or later policy results.

## Decision

V3 final-evaluation evidence may be authored only under the following rules.

1. **Fresh evidence only.** Every final-evaluation case is newly authored for V3 and uses the reserved `CRV3-201` through `CRV3-224` namespace.
2. **Authoring before scoring.** All 24 final-evaluation case pairs must exist and be frozen behind a final-evaluation manifest before the V3 artifact is assessed against them.
3. **Fixed allocation.** The corpus contains four capacity families, six cases per family, and four observations per case:
   - light capacity: `CRV3-201` through `CRV3-206`;
   - moderate capacity: `CRV3-207` through `CRV3-212`;
   - saturated capacity: `CRV3-213` through `CRV3-218`;
   - jagged capacity: `CRV3-219` through `CRV3-224`.
4. **Workload balance.** Each capacity family contains exactly two `structured_text`, two `code`, and two `open_ended_chat` cases.
5. **Runtime/outcome separation.** Runtime files may contain only lawful decision-time context. Candidate token IDs, observed acceptance labels, prefix-survival labels, and any post-hoc score inputs remain in separate outcome files.
6. **No refitting.** The V3 artifact, fit report, calibration manifest, and calibration case bytes are read-only throughout final-evidence authoring and assessment.
7. **No policy result yet.** Creating final-evaluation evidence does not create a policy score, scheduler result, promotion decision, capacity claim, or runtime-control eligibility.
8. **No V1/V2 data-bearing reuse.** V1 and V2 calibration/final-evaluation fixtures, labels, artifact parameters, and retained outcomes may not influence V3 final-evaluation case design.

## Consequences

- The final-evaluation corpus will be a fair one-time assessment input for V3 calibration.
- Any change to final-evaluation case bytes after its manifest is frozen invalidates the assessment and requires a new governed experiment boundary.
- Scheduler development remains blocked until the frozen V3 artifact passes its predeclared held-out calibration gate.

## Alternatives rejected

### Assess after each final-evaluation family

Rejected because incremental results could influence later final-evaluation authoring.

### Use V3 calibration cases as a final test

Rejected because the fitted artifact has already learned from them.

### Use V2 cases as V3 hidden evidence

Rejected because V2 is closed evidence and would contaminate the fresh V3 experiment.
