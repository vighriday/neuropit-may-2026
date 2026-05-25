"""Unit tests for the per driver persona prior loader and classifier.

These tests cover the contract every consumer of the prior system
relies on:

  * the loader returns sensible metadata regardless of whether a
    priors file exists,
  * a missing or malformed priors file falls back cleanly to
    population defaults,
  * the persona classifier produces deterministic labels for the
    same input regardless of whether `driver_id` is passed,
  * the threshold offsets actually shift the classification boundary
    for known cases.
"""

from __future__ import annotations

import json
import os
import textwrap

import pytest

from src.backend.common import persona, priors
from src.backend.common.weights import PERSONA


@pytest.fixture(autouse=True)
def _reset_cache():
    priors.reset_for_tests()
    yield
    priors.reset_for_tests()


def _write_priors(tmp_path, payload):
    path = tmp_path / "persona_priors.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_load_priors_missing_file_falls_back_to_defaults(tmp_path):
    missing = str(tmp_path / "does_not_exist.json")
    metadata = priors.load_priors(missing)
    assert metadata.available is False
    assert metadata.driver_count == 0
    assert metadata.path == missing
    # Driver thresholds for any id should equal the population default.
    assert priors.driver_thresholds("VER", PERSONA) == PERSONA


def test_load_priors_malformed_json_falls_back_to_defaults(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not valid json", encoding="utf-8")
    metadata = priors.load_priors(str(path))
    assert metadata.available is False
    assert priors.driver_thresholds("VER", PERSONA) == PERSONA


def test_load_priors_drivers_missing_section_falls_back(tmp_path):
    path = _write_priors(tmp_path, {"schema_version": 1, "drivers": "not a dict"})
    metadata = priors.load_priors(path)
    assert metadata.available is False
    assert priors.driver_thresholds("VER", PERSONA) == PERSONA


def test_load_priors_applies_offsets(tmp_path):
    payload = {
        "schema_version": 1,
        "source": {"year": 2099, "event": "Synth", "session": "R"},
        "drivers": {
            "HOT": {
                "panic_stress_offset": 5.0,
                "aggressive_stress_offset": 4.0,
                "defensive_confidence_offset": -3.0,
                "flow_confidence_offset": 2.0,
            },
            "COLD": {
                "panic_stress_offset": -5.0,
                "aggressive_stress_offset": -4.0,
                "defensive_confidence_offset": 3.0,
                "flow_confidence_offset": -2.0,
            },
        },
    }
    path = _write_priors(tmp_path, payload)
    metadata = priors.load_priors(path)
    assert metadata.available is True
    assert metadata.driver_count == 2
    assert metadata.source["event"] == "Synth"

    hot = priors.driver_thresholds("HOT", PERSONA)
    cold = priors.driver_thresholds("COLD", PERSONA)
    assert hot.panic_stress == PERSONA.panic_stress + 5.0
    assert cold.panic_stress == PERSONA.panic_stress - 5.0
    assert hot.aggressive_stress == PERSONA.aggressive_stress + 4.0
    assert cold.defensive_confidence == PERSONA.defensive_confidence + 3.0


def test_unknown_driver_falls_back_to_population_default(tmp_path):
    payload = {
        "schema_version": 1,
        "drivers": {"HOT": {"panic_stress_offset": 5.0}},
    }
    priors.load_priors(_write_priors(tmp_path, payload))
    assert priors.driver_thresholds("UNKNOWN_DRIVER", PERSONA) == PERSONA


def test_classify_without_driver_id_matches_legacy_behaviour():
    legacy = persona.classify(
        stress=90.0, confidence=20.0, fatigue=10.0, panic_oscillation=25.0, throttle_commitment=10.0
    )
    new = persona.classify(
        stress=90.0, confidence=20.0, fatigue=10.0, panic_oscillation=25.0, throttle_commitment=10.0,
        driver_id=None,
    )
    assert legacy == new == "Panic"


def test_priors_can_shift_a_driver_out_of_panic_classification(tmp_path):
    """A driver whose panic threshold is shifted up by ten points
    should stop being classified as Panic at exactly that boundary."""
    payload = {
        "schema_version": 1,
        "drivers": {
            "VER": {"panic_stress_offset": 10.0},
        },
    }
    priors.load_priors(_write_priors(tmp_path, payload))

    # Stress sits between the default (85) and the shifted (95).
    stress = 90.0
    panic_osc = 25.0  # well above the panic_oscillation threshold (20)

    # Default driver crosses Panic threshold.
    default_state = persona.classify(
        stress=stress, confidence=20.0, fatigue=10.0,
        panic_oscillation=panic_osc, throttle_commitment=10.0,
    )
    assert default_state == "Panic"

    # VER with a +10 panic offset stays below the panic threshold.
    ver_state = persona.classify(
        stress=stress, confidence=20.0, fatigue=10.0,
        panic_oscillation=panic_osc, throttle_commitment=10.0,
        driver_id="VER",
    )
    assert ver_state != "Panic"


def test_priors_metadata_keeps_audit_trail(tmp_path):
    payload = {
        "schema_version": 1,
        "source": {"year": 2024, "event": "Demo", "session": "Q"},
        "drivers": {"X": {"panic_stress_offset": 0.0}},
    }
    priors.load_priors(_write_priors(tmp_path, payload))
    snap = priors.priors_metadata()
    assert snap["available"] is True
    assert snap["driver_count"] == 1
    assert snap["source"] == {"year": 2024, "event": "Demo", "session": "Q"}
