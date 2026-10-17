"""
Dashboard (Flask + Leaflet) for the Ghazipur Landfill Fire & Contamination Shield.

Serves a live map of the 12 zones (coloured by Model A fire risk), the processing plants
with routing lines (Model B), and the resident alert + crew plan (Model C). A "heatwave"
slider raises temperatures / lowers humidity before prediction so risk, routes and alerts
change live. All sensor data is SIMULATED.

Pure-Python deps (Flask) so it runs on IBM LinuxONE / s390x. Run:
    python dashboard/app.py   ->   http://localhost:5000
"""

from pathlib import Path
import sys

from flask import Flask, jsonify, request, render_template

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "models"))

import joblib          # noqa: E402
import pandas as pd    # noqa: E402
from optimiser import optimise, load_plants  # noqa: E402
import genai           # noqa: E402

app = Flask(__name__)

_bundle = joblib.load(ROOT / "models" / "fire_model.joblib")
MODEL, FEATURES = _bundle["model"], _bundle["features"]
DF = pd.read_csv(ROOT / "data" / "landfill_sensors.csv", parse_dates=["timestamp"])
TIMESTAMPS = sorted(DF["timestamp"].unique())
PLANTS = load_plants()
GHAZIPUR = {"lat": 28.6257, "lon": 77.3277}


def color_for(risk: float) -> str:
    if risk >= 0.15:
        return "red"
    if risk >= 0.05:
        return "amber"
    return "green"


def apply_heatwave(rows, pct: float):
    rows = rows.copy()
    f = pct / 100.0
    rows["surface_temp_c"] = rows["surface_temp_c"] + f * 20.0
    rows["ambient_temp_c"] = rows["ambient_temp_c"] + f * 20.0
    rows["humidity_pct"] = (rows["humidity_pct"] - f * 40.0).clip(lower=5.0)
    return rows


def compute_state(hour_idx: int, heatwave_pct: float) -> dict:
    ts = TIMESTAMPS[hour_idx % len(TIMESTAMPS)]
    rows = DF[DF["timestamp"] == ts].sort_values("zone_id")
    rows = apply_heatwave(rows, heatwave_pct)

    proba = MODEL.predict_proba(rows[FEATURES])[:, 1]
    risks = {int(z): float(p) for z, p in zip(rows["zone_id"], proba)}
    zones = [{
        "zone_id": int(r.zone_id), "lat": float(r.zone_lat), "lon": float(r.zone_lon),
        "risk": round(risks[int(r.zone_id)], 3), "color": color_for(risks[int(r.zone_id)]),
    } for r in rows.itertuples()]

    # Higher fire risk (heatwave) -> excavate more aggressively to cut the fire load.
    # ASSUMPTION (documented in docs/SOURCES.md): target scales 8,000 -> 14,000 t/day.
    excavation_target = int(8_000 + (heatwave_pct / 100.0) * 6_000)
    plan = optimise(risks, excavation_target=excavation_target, incoming_textile=200, plants=PLANTS)

    top = max(risks, key=risks.get)
    wind = float(rows[rows["zone_id"] == top]["wind_direction_deg"].iloc[0])
    text = genai.generate(risks, plan, wind, use_llm=False)

    plant_tonnes = {}
    for rt in plan["routing"]:
        plant_tonnes[rt["plant_id"]] = plant_tonnes.get(rt["plant_id"], 0) + rt["tonnes"]
    plants_out = [{
        "plant_id": p["plant_id"], "name": p["name"], "type": p["type"],
        "lat": float(p["lat"]), "lon": float(p["lon"]),
        "tonnes": round(plant_tonnes.get(p["plant_id"], 0)),
    } for _, p in PLANTS.iterrows()]

    return {
        "timestamp": str(ts), "heatwave": heatwave_pct, "wind_from_deg": round(wind),
        "ghazipur": GHAZIPUR, "zones": zones, "plants": plants_out,
        "dig_order": plan["dig_order"], "routing": plan["routing"],
        "plant_utilisation": plan["plant_utilisation"],
        "unallocated": plan["unallocated_tonnes"],
        "total_unallocated": plan["total_unallocated_tonnes"],
        "resident_alert": text["resident_alert"], "crew_plan": text["crew_plan"],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state")
def api_state():
    hour = int(request.args.get("hour", 0))
    heat = float(request.args.get("heatwave", 0))
    return jsonify(compute_state(hour, heat))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
