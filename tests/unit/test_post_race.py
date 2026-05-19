"""Unit tests for the post race intelligence report builder."""

from __future__ import annotations

import json

from src.backend.config import get_settings
from src.backend.reporting import post_race


def _write_audit(path, events):
    with open(path / "cognitive-2026-05-19.jsonl", "w", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps(event) + "\n")


def test_empty_report_when_audit_dir_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIT_LOG_DIR", str(tmp_path / "nope"))
    get_settings.cache_clear()  # type: ignore[attr-defined]
    report = post_race.build_report()
    assert report["driver_count"] == 0
    assert report["drivers"] == {}
    get_settings.cache_clear()  # type: ignore[attr-defined]


def test_report_aggregates_per_driver(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIT_LOG_DIR", str(tmp_path))
    get_settings.cache_clear()  # type: ignore[attr-defined]
    events = [
        {
            "kind": "cognitive_evaluation",
            "driver_id": "VER",
            "timestamp": f"2026-05-19T12:00:0{i}Z",
            "state": {
                "stress_score": 50.0 + i,
                "confidence_score": 60.0,
                "fatigue_score": 10.0 + i,
                "panic_probability": 10.0 + i * 5,
                "emotional_drift_score": 5.0,
                "timestamp": f"2026-05-19T12:00:0{i}Z",
            },
            "inputs": {"features": {"session_id": "2021_AbuDhabi"}},
        }
        for i in range(5)
    ]
    events.append(
        {
            "kind": "explanation",
            "driver_id": "VER",
            "timestamp": "2026-05-19T12:00:05Z",
            "explanation": {"text": "stress climbing", "source": "stub"},
        }
    )
    _write_audit(tmp_path, events)

    report = post_race.build_report()
    assert report["driver_count"] == 1
    assert "VER" in report["drivers"]
    driver = report["drivers"]["VER"]
    assert driver["evaluation_count"] == 5
    assert driver["summary"]["avg_stress_score"] > 0.0
    assert driver["ghost_lap"] is not None
    assert len(driver["counterfactuals"]) == 5
    assert driver["explanations"][0]["text"] == "stress climbing"

    get_settings.cache_clear()  # type: ignore[attr-defined]


def test_session_filter(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIT_LOG_DIR", str(tmp_path))
    get_settings.cache_clear()  # type: ignore[attr-defined]
    events = [
        {
            "kind": "cognitive_evaluation",
            "driver_id": "VER",
            "timestamp": "2026-05-19T12:00:00Z",
            "state": {"stress_score": 40.0, "confidence_score": 60.0, "fatigue_score": 10.0, "panic_probability": 5.0, "emotional_drift_score": 1.0},
            "inputs": {"features": {"session_id": "race_A"}},
        },
        {
            "kind": "cognitive_evaluation",
            "driver_id": "HAM",
            "timestamp": "2026-05-19T13:00:00Z",
            "state": {"stress_score": 80.0, "confidence_score": 40.0, "fatigue_score": 60.0, "panic_probability": 35.0, "emotional_drift_score": 8.0},
            "inputs": {"features": {"session_id": "race_B"}},
        },
    ]
    _write_audit(tmp_path, events)

    report_a = post_race.build_report(session_id="race_A")
    report_b = post_race.build_report(session_id="race_B")
    assert list(report_a["drivers"].keys()) == ["VER"]
    assert list(report_b["drivers"].keys()) == ["HAM"]

    get_settings.cache_clear()  # type: ignore[attr-defined]
