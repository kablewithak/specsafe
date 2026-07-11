# Hugging Face Space Visual Direction

## Product goal

A new visitor should understand the result within roughly twenty seconds:

```text
adaptive verification sometimes helped
+ one governed loss remained visible
+ the real confidence candidate failed ranking safety
+ activation was blocked
```

## Visual character

The interface uses a dark editorial reliability-lab treatment rather than a generic analytics dashboard:

- warm amber for evidence and navigation;
- green for governed wins and passing movements;
- rose for the loss, failed safety gate, and blocked activation;
- large type and restrained cards for a case-study reading flow;
- no decorative imagery, stock assets, or model-brand styling;
- deliberate negative space and a clear mobile stack.

## Reading order

1. The tested question and blocked decision.
2. Three policy definitions.
3. Aggregate wins, neutral cases, and loss.
4. Six case-level utility comparisons.
5. Calibration improvements and ranking-safety failure.
6. Reliability interpretation.
7. Exact evidence boundary, claims, sources, and Dataset identity.

## Evidence behavior

The frontend must:

- parse the frozen index through a strict Zod contract;
- fail closed on unknown or invalid fields;
- display all six case identities;
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
- reduced-motion support;
- no horizontal overflow at mobile widths;
- text contrast suitable for a dark surface;
- charts accompanied by case cards and plain-language conclusions.

## Scope ceiling

This slice is a local visual shell. It does not include Hugging Face credentials, remote repository creation, deployment automation, analytics, a backend, or a publication claim.
