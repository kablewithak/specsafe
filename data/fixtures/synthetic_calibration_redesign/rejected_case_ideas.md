# Rejected Calibration Redesign Case Ideas

## Purpose

Record rejected ideas so later authoring does not quietly reintroduce leakage, ambiguity, or duplicate evidence.

| Rejected idea | Rejection reason | Permanent handling |
|---|---|---|
| Reuse the historical `STF-004` held-out trace shape. | It would turn consumed held-out evidence into an authoring template. | Prohibited. |
| Duplicate a calibration source-template fingerprint in a final-evaluation family. | It weakens family-level independence even when case IDs differ. | Prohibited and tested. |
| Place observed acceptance labels in runtime-input JSON. | Runtime policy boundaries must not receive post-hoc outcomes. | Prohibited by the existing strict runtime contract. |
| Add an extra final-evaluation case after artifact fitting. | It permits result-driven selection and invalidates the predeclared final boundary. | Requires a new governed fixture-set version. |
| Add indistinguishable high-confidence cases only to inflate sample count. | More repetitive cases do not create more diagnostic evidence. | Reject unless a distinct trace shape and ledger rationale exist. |
| Author a final case using a calibration prompt skeleton or token sequence. | It violates scenario-family isolation. | Prohibited. |

## Non-claims

This record does not establish that the proposed temperature method will pass held-out calibration fitness. It only preserves the anti-leakage decisions governing the next fixture-authoring stage.
