# Hugging Face Space Visual Direction

## Product goal

A new visitor should understand the north star and result within roughly twenty seconds:

```text
question=can adaptive verification spend compute more intelligently without future information
method=three policies on the same six governed cases
result=adaptive helped, matched, and lost depending on capacity
safety=the real confidence candidate failed ranking safety
outcome=activation blocked
```

The interface must explain the question before asking the visitor to interpret detailed evidence.

## Visual character

The interface uses a dark editorial reliability-lab treatment rather than a generic analytics dashboard:

- warm amber for the north star, evidence, and navigation;
- green for governed wins and passing movements;
- sky blue for neutral outcomes that must remain clearly visible;
- rose for the loss, failed safety gate, and blocked activation;
- large type and restrained cards for a case-study reading flow;
- no decorative imagery, stock assets, or model-brand styling;
- deliberate negative space and a clear mobile stack.

## Reading order

1. The tested question, short answer, and blocked decision.
2. The north star expressed as question, method, and answer.
3. Three policy definitions under one decision-time boundary.
4. A count scoreboard where wins, neutral cases, and losses are equally legible.
5. Explicit case buckets for both baseline comparisons.
6. Exact six-case utility values in a responsive comparison matrix.
7. Calibration improvements and ranking-safety failure.
8. Reliability interpretation.
9. Exact evidence boundary, claims, sources, and Dataset identity.

## Result-presentation rule

Do not use a grouped bar chart for the six cases. The wide negative range makes equal and near-zero outcomes visually disappear.

Use an exact comparison matrix instead:

- one row per governed case;
- fixed, static-threshold, and adaptive utility shown numerically;
- capacity condition and plain-language interpretation retained;
- adaptive-versus-fixed outcome shown as an explicit badge;
- mobile presentation uses stacked cards with the same values;
- neutral outcomes use a distinct visible treatment and are never represented as empty space.

## Evidence behavior

The frontend must:

- parse the frozen index through a strict Zod contract;
- fail closed on unknown or invalid fields;
- display all six case identities;
- keep `MPC5-101`, `MPC5-102`, and `MPC5-106` explicit as neutral versus fixed length;
- keep `MPC5-103` visible as the adaptive loss;
- keep `MPC5-104` and `MPC5-105` visible as adaptive wins;
- show `KEEP_DIAGNOSTIC_ONLY` and `ranking_safety_regression`;
- show the approximately `24.36x` ranking-safety breach;
- retain all supported claims and non-claims;
- perform no live inference, user-input collection, evidence mutation, or runtime research calculation.

## Responsive and accessibility rules

- semantic sections and headings;
- skip link and visible focus states;
- keyboard-operable tabs;
- semantic desktop table with a mobile card equivalent;
- reduced-motion support;
- no horizontal overflow at mobile widths;
- text contrast suitable for a dark surface;
- exact values accompanied by plain-language conclusions.

## Scope ceiling

This refinement changes narrative order and presentation only. It does not change the frozen evidence, add Hugging Face credentials, create a remote repository, add analytics, introduce a backend, or make a publication claim.
