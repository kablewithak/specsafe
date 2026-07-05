# V3 Separated Final-Evidence Index Contract

## Purpose

The V3 calibration corpus is frozen. The held-out final corpus needs its own authoring contract so final-case creation cannot mutate calibration provenance.

## Immutable calibration assets

The following files are read-only from this point onward:

```text
scenario_family_registry.json
calibration_manifest.json
evidence/calibration/quantile-isotonic-calibration-v1/artifact.json
evidence/calibration/quantile-isotonic-calibration-v1/fit_report.json
```

The calibration manifest must continue to rebuild byte-for-byte identically after each future V3 final-evidence slice.

## New final-evidence index

The next implementation slice will add a new, separate final-evidence authoring index under the V3 fixture root. It must contain:

- schema version;
- fixed final family IDs and reserved case IDs;
- split and data-role declarations;
- workload allocation per capacity family;
- authoring state for each family;
- explicit exclusions;
- no confidence values, candidate token IDs, labels, scores, calibration parameters, or scheduler actions.

The index must initially author only the light-capacity family:

```text
CRV3-201 through CRV3-206
2 structured_text cases
2 code cases
2 open_ended_chat cases
```

Moderate, saturated, jagged, and adversarial case files remain absent.

## Allowed dependency direction

```text
frozen calibration registry + calibration manifest
  -> frozen quantile-isotonic artifact

separate final-evidence index
  -> held-out runtime/outcome case pairs
  -> final-evaluation manifest
  -> one held-out calibration assessment
  -> policy comparison
```

The final-evidence path may verify that the frozen calibration assets exist and match their known hashes. It may not rewrite or absorb them.
