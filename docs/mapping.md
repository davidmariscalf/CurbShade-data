# Field mapping

CurbShade uses a normalized internal segment model.

| CurbShade | Typical source |
|---|---|
| `length_m` | OSMnx edge length |
| `slope_pct` | `incline` or locally derived elevation |
| `curb_cm` | curb/kerb height observation |
| `width_m` | sidewalk/path width |
| `surface_score` | normalized surface traversability |
| `shade_fraction` | local canopy/building/shade model |
| `crossing_risk` | crossing metadata / local model |

The normalizer deliberately leaves unsupported or absent values as `null`. Filling missing curb values with zero would create false accessibility.
