from __future__ import annotations
import json

graph = {
    "schema_version": "curbshade-network/1",
    "nodes": [{"id": x} for x in ["A", "B", "C", "D", "E"]],
    "edges": [
        {"u":"A","v":"B","length_m":70,"slope_pct":2.0,"curb_cm":0.0,"width_m":1.5,"surface_score":0.9,"shade_fraction":0.1,"crossing_risk":0.1},
        {"u":"B","v":"E","length_m":70,"slope_pct":2.0,"curb_cm":5.0,"width_m":1.5,"surface_score":0.9,"shade_fraction":0.1,"crossing_risk":0.1},
        {"u":"A","v":"C","length_m":90,"slope_pct":3.0,"curb_cm":0.0,"width_m":1.4,"surface_score":0.9,"shade_fraction":0.85,"crossing_risk":0.05},
        {"u":"C","v":"D","length_m":70,"slope_pct":3.0,"curb_cm":0.0,"width_m":1.4,"surface_score":0.9,"shade_fraction":0.9,"crossing_risk":0.05},
        {"u":"D","v":"E","length_m":40,"slope_pct":2.0,"curb_cm":0.0,"width_m":1.4,"surface_score":0.9,"shade_fraction":0.8,"crossing_risk":0.05}
    ]
}
print(json.dumps(graph, indent=2))
