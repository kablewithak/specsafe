# Hugging Face Space Visual Direction

## Status

Approved product direction. Implementation begins only after the Dataset publication is remotely
verified.

## Quick experience goal

A visitor should understand the project in about 20 seconds:

> Adaptive verification helped under some conditions, was neutral under others, and lost in one.
> When the real confidence signal failed its safety gate, SpecSafe blocked activation.

The Space must feel like a polished visual case study, not an academic paper viewer or monitoring
dashboard.

## Product principles

- Lead with a short plain-language summary.
- Guide the visitor through one story rather than presenting an unexplained dashboard.
- Keep technical evidence available through expandable details.
- Make the difference between a useful scheduler and a failed confidence candidate obvious.
- Design mobile-first for portfolio and LinkedIn visitors.
- Use accessible labels in addition to colour.
- Keep all interactions read-only and evidence-backed.

## Visual direction

- React, Vite, TypeScript, Tailwind CSS, shadcn/ui, and Recharts.
- Calm editorial layout with generous spacing and strong typography.
- Warm off-white and deep slate surfaces with restrained blue, teal, amber, and red accents.
- Rounded cards, subtle depth, clean dividers, and purposeful micro-interactions.
- No particle effects, chatbot panel, fake live telemetry, or crowded enterprise-dashboard styling.
- Every chart must include a readable plain-language summary.

## Guided page flow

1. Quick summary and main conclusion.
2. What SpecSafe tested.
3. Wins, draws, and losses against the two baselines.
4. Where adaptive scheduling helped and where it did not.
5. Why the real confidence candidate was blocked.
6. What the findings mean for broader AI systems.
7. Optional evidence explorer and reproduction details.

## Core visuals

- Grouped utility bars by capacity condition.
- Simple win, draw, and loss summary.
- Raw-versus-calibrated metric comparison with metric direction explained.
- Ranking-safety gate showing observed versus permitted degradation.
- A clear causal-safe versus retrospective-unsafe flow.

## Interaction boundary

Allowed interactions include filtering capacity conditions, switching baselines, opening evidence
cards, viewing exact values, and copying artifact identifiers. No live inference, uploaded traces,
threshold tuning, optimizer, or evidence-changing controls belong in the first Space release.
