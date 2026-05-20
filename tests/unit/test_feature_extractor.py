"""Tests for the lightweight feature extractor.

The cognitive engine reads ``panic_oscillation``, ``throttle_commitment``,
and ``braking_hesitation`` from the feature stream. The extractor emits
those fields directly. These tests pin the contract so the two files
cannot silently drift.
"""

from __future__ import annotations

import math
from typing import Dict, List

import pytest

from src.backend.inference.feature_extractor import FeatureExtractor


@pytest.fixture()
def extractor(monkeypatch: pytest.MonkeyPatch) -> FeatureExtractor:
    instance = FeatureExtractor.__new__(FeatureExtractor)
    instance.broker_url = "memory:0"
    instance.history = {}
    return instance


def _windowed_frame(steering: float, throttle: float, brake: float, speed: float) -> Dict:
    return {
        "timestamp": "2026-05-20T13:00:00Z",
        "steering_angle": steering,
        "throttle": throttle,
        "brake": brake,
        "speed": speed,
    }


def _fill_window(extractor: FeatureExtractor, driver: str, frames: List[Dict]) -> Dict:
    last = None
    for frame in frames:
        last = extractor.extract_features(driver, frame)
    assert last is not None
    return last


def test_extractor_emits_renamed_cognitive_fields():
    extractor = FeatureExtractor.__new__(FeatureExtractor)
    extractor.broker_url = "memory:0"
    extractor.history = {}
    frames = [
        _windowed_frame(steering=math.sin(i / 3.0), throttle=80.0 - i * 2, brake=10.0 + i, speed=200.0 - i)
        for i in range(15)
    ]
    features = _fill_window(extractor, "VER", frames)
    # Every consumer-facing field the cognitive engine reads must exist.
    for key in (
        "steering_instability",
        "micro_correction_freq",
        "braking_variance",
        "throttle_jitter",
        "throttle_commitment",
        "braking_hesitation",
        "panic_oscillation",
        "panic_signature",
    ):
        assert key in features, f"missing field {key}"
        assert isinstance(features[key], float), f"{key} should be float"


def test_throttle_commitment_normalised_to_unit_interval():
    extractor = FeatureExtractor.__new__(FeatureExtractor)
    extractor.broker_url = "memory:0"
    extractor.history = {}
    frames = [_windowed_frame(steering=0.1 * i, throttle=100.0, brake=0.0, speed=300.0) for i in range(12)]
    features = _fill_window(extractor, "HAM", frames)
    assert 0.95 <= features["throttle_commitment"] <= 1.0


def test_panic_signature_alias_matches_panic_oscillation():
    extractor = FeatureExtractor.__new__(FeatureExtractor)
    extractor.broker_url = "memory:0"
    extractor.history = {}
    frames = [_windowed_frame(steering=math.sin(i), throttle=50.0, brake=20.0, speed=200.0) for i in range(15)]
    features = _fill_window(extractor, "LEC", frames)
    assert features["panic_signature"] == features["panic_oscillation"]


def test_extractor_returns_none_before_window_is_full():
    extractor = FeatureExtractor.__new__(FeatureExtractor)
    extractor.broker_url = "memory:0"
    extractor.history = {}
    for i in range(5):
        result = extractor.extract_features("NOR", _windowed_frame(0.0, 50.0, 10.0, 200.0))
    assert result is None
