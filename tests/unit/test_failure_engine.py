"""Unit tests for the predictive failure engine.

We exercise the forecasting maths directly, bypassing the Kafka loop, so the
tests stay fast and deterministic.
"""

from __future__ import annotations

from src.backend.prediction.failure_engine import HORIZONS, PredictiveFailureEngine


def _state(**overrides) -> dict:
    base = {
        "driver_id": "VER",
        "timestamp": "2026-05-19T12:00:00Z",
        "stress_score": 50.0,
        "confidence_score": 60.0,
        "fatigue_score": 30.0,
        "tunnel_vision_prob": 0.0,
        "persona_state": "Recovery",
        "confidence_band": "moderate",
    }
    base.update(overrides)
    return base


def _engine() -> PredictiveFailureEngine:
    engine = PredictiveFailureEngine.__new__(PredictiveFailureEngine)
    engine.history = {}
    from collections import defaultdict, deque
    engine.history = defaultdict(lambda: deque(maxlen=PredictiveFailureEngine.BUFFER_LENGTH))
    return engine


def test_forecast_returns_every_horizon():
    engine = _engine()
    payload = engine.forecast(_state())
    assert payload["kind"] == "failure_forecast"
    assert set(payload["horizons"].keys()) == set(HORIZONS)


def test_probabilities_stay_within_unit_range():
    engine = _engine()
    payload = engine.forecast(_state(stress_score=99.0, confidence_score=5.0, fatigue_score=95.0, tunnel_vision_prob=100.0, persona_state="Panic"))
    for horizon, scores in payload["horizons"].items():
        for name, value in scores.items():
            assert 0.0 <= value <= 1.0, f"{horizon}.{name} = {value} out of range"


def test_panic_persona_raises_spin_probability():
    engine = _engine()
    calm = engine.forecast(_state(stress_score=20.0, confidence_score=90.0, persona_state="Flow State"))
    panic = engine.forecast(_state(stress_score=90.0, confidence_score=20.0, persona_state="Panic", tunnel_vision_prob=100.0))
    assert panic["horizons"]["5s"]["spin_probability"] > calm["horizons"]["5s"]["spin_probability"]


def test_horizon_weight_decays_with_distance():
    engine = _engine()
    payload = engine.forecast(_state(stress_score=80.0, confidence_score=30.0, persona_state="Aggressive"))
    five_sec = payload["horizons"]["5s"]["crash_likelihood"]
    full_race = payload["horizons"]["full_race"]["crash_likelihood"]
    assert five_sec >= full_race


def test_engine_pulls_constants_from_weights_module():
    import pytest

    from src.backend.common import weights

    engine = _engine()
    fw = weights.FAILURE
    payload = engine.forecast(
        _state(stress_score=100.0, confidence_score=0.0, tunnel_vision_prob=100.0, persona_state="Aggressive")
    )
    # crash_likelihood at the 5s horizon is the convex blend clamped to 1
    # then scaled by horizon_5s. With all three inputs maxed it must
    # equal the sum of crash_tunnel + crash_stress + crash_inv_confidence
    # clamped to 1, scaled by horizon_5s.
    expected = min(fw.crash_tunnel + fw.crash_stress + fw.crash_inv_confidence, 1.0) * fw.horizon_5s
    assert payload["horizons"]["5s"]["crash_likelihood"] == pytest.approx(expected, abs=1e-3)
