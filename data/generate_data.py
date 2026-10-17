"""
Synthetic sensor-data generator for the Ghazipur Landfill Fire & Contamination Shield
(IBM Z Datathon 2026, Theme 1).

Produces hourly readings for 12 landfill zones over 90 days (2026-04-01 onward, so the
window spans the hot pre-monsoon April-June period). Fire risk is driven by high methane,
high surface temperature, low humidity and long dry spells, plus random noise.

SYNTHETIC DATA — disclosed as synthetic. Not real sensor measurements. Real NASA FIRMS
fire detections and Open-Meteo weather are used elsewhere as supporting evidence.

Dependencies: pandas, numpy only.

Output: data/landfill_sensors.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

# --- configuration -----------------------------------------------------------
N_ZONES = 12
DAYS = 90
HOURS = DAYS * 24
START = pd.Timestamp("2026-04-01 00:00:00")
TARGET_FIRE_RATE = 0.065  # aim for the middle of the 5-8% band

# Ghazipur landfill bounding box
LAT_MIN, LAT_MAX = 28.623, 28.628
LON_MIN, LON_MAX = 77.325, 77.330

OUT_PATH = Path(__file__).resolve().parent / "landfill_sensors.csv"


def build_zone_coords():
    """12 zones laid out on a 3x4 grid inside the bounding box, with small jitter."""
    grid_lat = np.linspace(LAT_MIN + 0.0006, LAT_MAX - 0.0006, 3)
    grid_lon = np.linspace(LON_MIN + 0.0006, LON_MAX - 0.0006, 4)
    coords = np.array([(la, lo) for la in grid_lat for lo in grid_lon])
    coords[:, 0] += RNG.normal(0, 0.0002, N_ZONES)
    coords[:, 1] += RNG.normal(0, 0.0002, N_ZONES)
    coords[:, 0] = np.clip(coords[:, 0], LAT_MIN, LAT_MAX)
    coords[:, 1] = np.clip(coords[:, 1], LON_MIN, LON_MAX)
    return coords


def build_time_series():
    """Shared, site-level time features: timestamps, seasonal/diurnal temp, rain."""
    timestamps = START + pd.to_timedelta(np.arange(HOURS), unit="h")
    doy = timestamps.dayofyear.to_numpy()
    hour = timestamps.hour.to_numpy()

    # Seasonal mean temp: hot through Apr-Jun, peaking late May (pre-monsoon).
    seasonal = 30.0 + 9.0 * np.sin(np.pi * (doy - 91) / 120.0)
    # Diurnal swing, peaking ~15:00.
    diurnal = 7.0 * np.sin(2 * np.pi * (hour - 9) / 24.0)
    ambient_base = seasonal + diurnal

    # Daytime solar loading on the landfill surface (bakes hard midday).
    solar = 14.0 * np.clip(np.sin(np.pi * (hour - 6) / 12.0), 0, None)

    # Rain: very rare in the dry season, ramping up as the monsoon approaches (late June).
    p_rain = 0.002 + 0.020 * np.clip((doy - 160) / 21.0, 0, 1)
    rain = RNG.random(HOURS) < p_rain

    days_since_rain = np.empty(HOURS)
    cur = 10.0  # assume ~10 dry days before the window starts
    for i in range(HOURS):
        cur = 0.0 if rain[i] else cur + 1.0 / 24.0
        days_since_rain[i] = cur

    return timestamps, ambient_base, solar, days_since_rain


def generate():
    coords = build_zone_coords()
    zone_methane_base = RNG.uniform(400, 2600, N_ZONES)  # some zones run hotter
    timestamps, ambient_base, solar, days_since_rain = build_time_series()

    frames = []
    for z in range(N_ZONES):
        # Warmer air -> more microbial activity -> more methane.
        methane = (
            zone_methane_base[z] * (1.0 + 0.015 * (ambient_base - 30.0))
            + RNG.normal(0, 150, HOURS)
        )
        methane = np.clip(methane, 50, None)

        ambient = ambient_base + RNG.normal(0, 1.0, HOURS)
        surface = (
            ambient + 0.004 * methane + solar + RNG.normal(0, 2.0, HOURS)
        )

        rain_boost = 30.0 * np.exp(-days_since_rain / 2.0)
        humidity = np.clip(
            70.0 - 1.2 * (ambient - 25.0) + rain_boost + RNG.normal(0, 5.0, HOURS),
            5, 100,
        )

        wind_speed = np.clip(RNG.gamma(2.0, 5.0, HOURS), 0, 45)
        wind_direction = RNG.uniform(0, 360, HOURS)

        frames.append(pd.DataFrame({
            "timestamp": timestamps,
            "zone_id": z + 1,
            "zone_lat": round(coords[z, 0], 6),
            "zone_lon": round(coords[z, 1], 6),
            "methane_ppm": methane,
            "surface_temp_c": surface,
            "ambient_temp_c": ambient,
            "humidity_pct": humidity,
            "wind_speed_kmh": wind_speed,
            "wind_direction_deg": wind_direction,
            "days_since_rain": days_since_rain,
        }))

    df = pd.concat(frames, ignore_index=True)

    # --- fire label: logistic risk from the key drivers + noise ---------------
    def z_score(s):
        return (s - s.mean()) / s.std()

    score = (
        0.9 * z_score(df["methane_ppm"])
        + 1.1 * z_score(df["surface_temp_c"])
        - 0.8 * z_score(df["humidity_pct"])
        + 0.7 * z_score(df["days_since_rain"])
        + RNG.normal(0, 0.5, len(df))
    ).to_numpy()

    # Solve the intercept so the mean fire probability hits the target rate.
    lo, hi = -15.0, 5.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if (1.0 / (1.0 + np.exp(-(score + mid)))).mean() > TARGET_FIRE_RATE:
            hi = mid
        else:
            lo = mid
    intercept = (lo + hi) / 2.0
    prob = 1.0 / (1.0 + np.exp(-(score + intercept)))
    df["fire_next_24h"] = (RNG.random(len(df)) < prob).astype(int)

    # Tidy numeric precision.
    df["methane_ppm"] = df["methane_ppm"].round(1)
    df["surface_temp_c"] = df["surface_temp_c"].round(2)
    df["ambient_temp_c"] = df["ambient_temp_c"].round(2)
    df["humidity_pct"] = df["humidity_pct"].round(1)
    df["wind_speed_kmh"] = df["wind_speed_kmh"].round(1)
    df["wind_direction_deg"] = df["wind_direction_deg"].round(1)
    df["days_since_rain"] = df["days_since_rain"].round(2)

    return df


def summarise(df):
    fire_rate = df["fire_next_24h"].mean()
    print("=" * 60)
    print("SYNTHETIC LANDFILL SENSOR DATA  (disclosed as synthetic)")
    print("=" * 60)
    print(f"Rows:              {len(df):,}")
    print(f"Zones:             {df['zone_id'].nunique()}")
    print(f"Date range:        {df['timestamp'].min()}  ->  {df['timestamp'].max()}")
    print(f"Fire rate:         {fire_rate:.2%}  ({int(df['fire_next_24h'].sum()):,} fire rows)")
    print()

    drivers = ["methane_ppm", "surface_temp_c", "humidity_pct",
               "days_since_rain", "wind_speed_kmh"]
    means = df.groupby("fire_next_24h")[drivers].mean().round(2)
    means.index = ["no fire (0)", "fire (1)"]
    print("Average driver values, fire vs no-fire:")
    print(means.T.to_string())
    print("=" * 60)


if __name__ == "__main__":
    df = generate()
    df.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(df):,} rows -> {OUT_PATH}\n")
    summarise(df)
