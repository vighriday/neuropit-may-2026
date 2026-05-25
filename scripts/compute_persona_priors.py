"""Compute per-driver persona priors from real F1 session telemetry.

Why this script exists
----------------------
The default `PersonaThresholds` in `src/backend/common/weights.py` are
calibrated against a population-level average driver. In reality each
driver has a distinct telemetry signature: a calm driver running clean
laps in a quick car sits in a different operating envelope than a
desperate driver hustling a slower car. Applying the same absolute
stress / confidence thresholds to everyone over-classifies aggressive
drivers as "Panic" and conservative drivers as "Defensive".

This script generates a per-driver delta against the population
defaults, computed from FastF1 telemetry for a configurable session.
The deltas are saved to `data/persona_priors.json` and loaded at
cognitive engine startup. If the file is missing the engine falls
back to the population defaults so the project still runs on a fresh
clone without any priors at all.

How the deltas are computed
---------------------------
For every driver we extract a "stress proxy" feature vector per lap:

    steering_proxy = stdev of throttle pedal trace over the lap
    braking_proxy  = stdev of brake trace over the lap
    speed_proxy    = mean speed normalised by session mean

We then compute a robust median per driver (resistant to a single
crash lap polluting the average) and store the z-score against the
session-wide median. A positive z means the driver runs hotter than
the average across this session; negative means calmer.

We translate the z-scores into threshold offsets:

    persona_priors[driver]["panic_stress_offset"]  = +z * 6.0
    persona_priors[driver]["aggressive_stress_offset"] = +z * 5.0
    persona_priors[driver]["defensive_confidence_offset"] = -z * 4.0
    persona_priors[driver]["flow_confidence_offset"] = +z * 3.0

A driver whose proxy stdev sits above the session median needs a
higher stress threshold before they get tagged "Panic", since their
baseline already runs hot. A driver below the median gets the
threshold pulled down. This is the standard z-score normalisation
approach used in any reasonable per-subject baseline calibration.

Re-running this script
----------------------
The generated artifact is checked in for reproducibility, but anyone
with FastF1 access can re-generate it by running:

    python -m scripts.compute_persona_priors --year 2021 --event "Abu Dhabi"

The defaults match the playback session NeuroPit ships with so the
priors line up with the demo data out of the box. Use `--out` to
write to a non-default path.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import statistics
from typing import Dict, List

import warnings

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

_DEFAULTS_DOC = (
    "Population defaults (PersonaThresholds in src/backend/common/weights.py): "
    "panic_stress=85, aggressive_stress=70, defensive_confidence=50, flow_confidence=80."
)


def _proxy_features(lap_telemetry) -> Dict[str, float]:
    """Compute a small proxy feature vector for a single lap."""
    throttle = lap_telemetry.get("Throttle")
    brake = lap_telemetry.get("Brake")
    speed = lap_telemetry.get("Speed")

    out = {}
    if throttle is not None and len(throttle) > 5:
        out["throttle_stdev"] = float(statistics.pstdev(throttle))
    if brake is not None and len(brake) > 5:
        # Brake on FastF1 is a 0/1 channel. stdev captures rapid on/off cycles.
        out["brake_stdev"] = float(statistics.pstdev([float(b) for b in brake]))
    if speed is not None and len(speed) > 5:
        out["mean_speed"] = float(statistics.mean(speed))
    return out


def _driver_median(per_lap_features: List[Dict[str, float]]) -> Dict[str, float]:
    """Median across laps for each proxy feature, ignoring missing laps."""
    if not per_lap_features:
        return {}
    keys = set()
    for lap in per_lap_features:
        keys.update(lap.keys())
    out = {}
    for key in keys:
        values = [lap[key] for lap in per_lap_features if key in lap]
        if values:
            out[key] = float(statistics.median(values))
    return out


def _z(value: float, population: List[float]) -> float:
    if len(population) < 2:
        return 0.0
    pop_mean = statistics.mean(population)
    pop_stdev = statistics.pstdev(population)
    if pop_stdev == 0:
        return 0.0
    return (value - pop_mean) / pop_stdev


def compute_priors(year: int, event: str, session: str = "R") -> Dict[str, Dict[str, float]]:
    """Run the FastF1 load and emit the priors dict.

    The function is structured so the test suite can stub the FastF1
    session with a deterministic fixture if needed.
    """
    import fastf1

    cache_path = os.environ.get("FASTF1_CACHE_DIR", "fastf1_cache")
    fastf1.Cache.enable_cache(cache_path)

    logger.info("Loading FastF1 session %s %s %s", year, event, session)
    sess = fastf1.get_session(year, event, session)
    sess.load(telemetry=True, laps=True, weather=False, messages=False)

    driver_ids = list(sess.drivers)
    if not driver_ids:
        raise RuntimeError("FastF1 returned no drivers for the requested session")

    # Map FastF1 numeric driver codes to canonical three-letter codes.
    driver_codes: Dict[str, str] = {}
    per_driver_median: Dict[str, Dict[str, float]] = {}

    for code in driver_ids:
        laps = sess.laps.pick_drivers([code])
        if laps.empty:
            continue
        three_letter = laps.iloc[0]["Driver"]
        if not isinstance(three_letter, str) or not three_letter:
            continue

        per_lap_features: List[Dict[str, float]] = []
        for _, lap in laps.iterrows():
            try:
                car_data = lap.get_car_data()
                per_lap_features.append(_proxy_features(car_data))
            except Exception as exc:
                logger.debug("Skipping lap for %s: %s", three_letter, exc)
                continue

        median = _driver_median(per_lap_features)
        if not median:
            continue
        driver_codes[code] = three_letter
        per_driver_median[three_letter] = median

    if not per_driver_median:
        raise RuntimeError("No driver telemetry could be extracted from the session")

    # Build population distributions for each proxy feature.
    feature_keys = {key for medians in per_driver_median.values() for key in medians.keys()}
    populations: Dict[str, List[float]] = {key: [] for key in feature_keys}
    for medians in per_driver_median.values():
        for key in feature_keys:
            if key in medians:
                populations[key].append(medians[key])

    # Compute z-scores and translate into threshold offsets per driver.
    priors: Dict[str, Dict[str, float]] = {}
    for driver, medians in per_driver_median.items():
        z_throttle = _z(medians.get("throttle_stdev", 0.0), populations.get("throttle_stdev", [])) if "throttle_stdev" in medians else 0.0
        z_brake = _z(medians.get("brake_stdev", 0.0), populations.get("brake_stdev", [])) if "brake_stdev" in medians else 0.0
        # A driver who runs hotter throttle and brake stdevs is the
        # "hot operating envelope" archetype. Their stress thresholds
        # need to lift before they get classified Panic. A driver who
        # runs cooler is the opposite.
        hot_z = (z_throttle + z_brake) / 2.0

        priors[driver] = {
            "panic_stress_offset": round(hot_z * 6.0, 2),
            "aggressive_stress_offset": round(hot_z * 5.0, 2),
            "defensive_confidence_offset": round(-hot_z * 4.0, 2),
            "flow_confidence_offset": round(hot_z * 3.0, 2),
            "hot_envelope_z": round(hot_z, 3),
            "proxy_medians": {k: round(v, 3) for k, v in medians.items()},
        }

    return priors


def write_priors(priors: Dict[str, Dict[str, float]], path: str, source: dict) -> None:
    payload = {
        "schema_version": 1,
        "source": source,
        "documentation": _DEFAULTS_DOC,
        "drivers": priors,
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    logger.info("Wrote priors for %d drivers to %s", len(priors), path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2021)
    parser.add_argument("--event", type=str, default="Abu Dhabi")
    parser.add_argument("--session", type=str, default="R")
    parser.add_argument("--out", type=str, default="data/persona_priors.json")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    priors = compute_priors(args.year, args.event, args.session)
    write_priors(
        priors,
        args.out,
        source={"year": args.year, "event": args.event, "session": args.session},
    )


if __name__ == "__main__":
    main()
