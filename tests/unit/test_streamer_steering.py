"""Tests for the steering angle proxy that the streamer derives."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.backend.ingestion.streamer import HistoricalRaceStreamer


def test_steering_proxy_is_zero_for_straight_line():
    df = pd.DataFrame(
        {
            "X": np.linspace(0.0, 1000.0, 50),
            "Y": np.zeros(50),
            "Speed": np.full(50, 300.0),
            "Throttle": np.full(50, 100.0),
            "Brake": np.zeros(50),
        }
    )
    enriched = HistoricalRaceStreamer._enrich_with_steering(df)
    # A straight line should produce zero steering. The first sample may
    # carry a tiny artefact from the prepend, so we check the bulk.
    assert np.allclose(enriched["steering_angle"].iloc[1:], 0.0, atol=1e-6)


def test_steering_proxy_picks_up_a_left_turn():
    angles = np.linspace(0.0, math.pi / 2.0, 80)
    radius = 50.0
    df = pd.DataFrame(
        {
            "X": radius * np.cos(angles),
            "Y": radius * np.sin(angles),
            "Speed": np.full(80, 200.0),
            "Throttle": np.full(80, 80.0),
            "Brake": np.zeros(80),
        }
    )
    enriched = HistoricalRaceStreamer._enrich_with_steering(df)
    # A constant radius turn produces a constant non-zero steering signal.
    steering = enriched["steering_angle"].iloc[5:]
    assert (steering.abs() > 0.5).all()


def test_steering_proxy_clipped_to_max_wheel_lock():
    df = pd.DataFrame(
        {
            "X": np.array([0.0, 100.0, -100.0, 200.0, -200.0]),
            "Y": np.array([0.0, 100.0, -100.0, 200.0, -200.0]),
            "Speed": np.full(5, 50.0),
            "Throttle": np.full(5, 50.0),
            "Brake": np.zeros(5),
        }
    )
    enriched = HistoricalRaceStreamer._enrich_with_steering(df)
    assert enriched["steering_angle"].abs().max() <= 180.0


def test_steering_proxy_handles_missing_columns():
    df = pd.DataFrame({"Speed": [100.0, 200.0], "Throttle": [50.0, 60.0], "Brake": [0.0, 0.0]})
    enriched = HistoricalRaceStreamer._enrich_with_steering(df)
    assert "steering_angle" in enriched.columns
    assert (enriched["steering_angle"] == 0.0).all()
