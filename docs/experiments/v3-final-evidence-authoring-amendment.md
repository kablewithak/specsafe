# V3 Final-Evidence Authoring Amendment

## Why this amendment exists

The original V3 plan correctly froze calibration evidence before final evidence. A later implementation detail became clear: the calibration manifest hashes the shared V3 registry. Updating that shared registry during final-case authoring would alter calibration provenance.

This amendment keeps the research rule intact while improving the harness boundary.

## Authoring rules

1. Leave the frozen calibration registry, calibration manifest, fitted artifact, and fit report unchanged.
2. Introduce a separate final-evidence index before any held-out case bytes exist.
3. Author all six light-capacity case pairs before reading the fitted artifact against any one of them.
4. Do not create a final-evaluation manifest until all 24 final case pairs are authored.
5. Do not run a held-out calibration assessment until the full 24-case manifest is frozen.
6. Do not implement scheduler or policy-comparison behavior until the held-out calibration gate is retained.

## Evidence status

No V3 held-out case has been assessed. No V3 final result exists. No adaptive-policy claim is authorised.
