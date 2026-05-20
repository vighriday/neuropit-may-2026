"""Tests for the post race lap time estimator.

The previous implementation hardcoded a 90 second lap. The current
helper derives lap time from the wall clock span between the first and
last audit row in the window the caller passed in. This file pins that
contract so we never regress to a fictional placeholder.
"""

from __future__ import annotations

from src.backend.reporting.post_race import _estimate_lap_time_s


def _row(timestamp: str) -> dict:
    return {"timestamp": timestamp, "kind": "cognitive_evaluation"}


def test_returns_zero_when_no_events():
    assert _estimate_lap_time_s([]) == 0.0


def test_returns_zero_with_single_event():
    assert _estimate_lap_time_s([_row("2026-05-20T13:00:00Z")]) == 0.0


def test_returns_wall_clock_span_across_window():
    events = [
        _row("2026-05-20T13:00:00Z"),
        _row("2026-05-20T13:00:15Z"),
        _row("2026-05-20T13:01:30Z"),
    ]
    assert _estimate_lap_time_s(events) == 90.0


def test_handles_unparseable_timestamps_gracefully():
    events = [
        _row("not a date"),
        _row("2026-05-20T13:00:00Z"),
        _row("2026-05-20T13:00:45Z"),
        _row(""),
    ]
    assert _estimate_lap_time_s(events) == 45.0


def test_never_returns_a_negative_span():
    events = [
        _row("2026-05-20T13:00:00Z"),
        _row("2026-05-20T13:00:00Z"),
    ]
    assert _estimate_lap_time_s(events) == 0.0
