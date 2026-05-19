"""Counterfactual Simulation Engine.

Generates alternate realities from a baseline cognitive lap summary by
applying small, interpretable adjustments to the inputs. The PRD lists the
canonical scenarios in section twenty. The implementation honours that list
and refuses to invent new ones at runtime so the audit log stays clean.

A counterfactual is not a prediction. It is a what if. Every output carries
the scenario name, the adjustments that were applied, and the resulting lap
delta so the strategist can see exactly what changed and why.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

from src.backend.simulation.ghost_lap import LapCognitiveSummary, attribute_lost_time


SCENARIOS = (
    "earlier_pit_stop",
    "lower_fatigue",
    "stable_emotional_state",
    "delayed_rain_onset",
    "reduced_pressure_environment",
)


@dataclass
class CounterfactualResult:
    scenario: str
    baseline_lap_time_s: float
    counterfactual_lap_time_s: float
    lap_delta_s: float
    rationale: str
    adjustments: Dict[str, float] = field(default_factory=dict)


def _adjust(summary: LapCognitiveSummary, **changes) -> LapCognitiveSummary:
    return LapCognitiveSummary(
        lap_number=summary.lap_number,
        driver_id=summary.driver_id,
        actual_lap_time_s=changes.get("actual_lap_time_s", summary.actual_lap_time_s),
        average_stress=changes.get("average_stress", summary.average_stress),
        average_fatigue=changes.get("average_fatigue", summary.average_fatigue),
        panic_events=changes.get("panic_events", summary.panic_events),
    )


def _earlier_pit_stop(summary: LapCognitiveSummary) -> CounterfactualResult:
    adjusted = _adjust(
        summary,
        average_fatigue=summary.average_fatigue * 0.6,
        average_stress=summary.average_stress * 0.85,
    )
    baseline = attribute_lost_time(summary)
    after = attribute_lost_time(adjusted)
    return CounterfactualResult(
        scenario="earlier_pit_stop",
        baseline_lap_time_s=baseline.actual_lap_time_s,
        counterfactual_lap_time_s=after.ghost_lap_time_s,
        lap_delta_s=round(after.ghost_lap_time_s - baseline.actual_lap_time_s, 3),
        rationale="Lower fatigue and stress after an earlier pit window reduces cognitive lost time.",
        adjustments={"fatigue_multiplier": 0.6, "stress_multiplier": 0.85},
    )


def _lower_fatigue(summary: LapCognitiveSummary) -> CounterfactualResult:
    adjusted = _adjust(summary, average_fatigue=max(summary.average_fatigue - 25.0, 0.0))
    baseline = attribute_lost_time(summary)
    after = attribute_lost_time(adjusted)
    return CounterfactualResult(
        scenario="lower_fatigue",
        baseline_lap_time_s=baseline.actual_lap_time_s,
        counterfactual_lap_time_s=after.ghost_lap_time_s,
        lap_delta_s=round(after.ghost_lap_time_s - baseline.actual_lap_time_s, 3),
        rationale="Lower fatigue removes cognitive lost time attributed to steering loss.",
        adjustments={"fatigue_delta": -25.0},
    )


def _stable_emotional_state(summary: LapCognitiveSummary) -> CounterfactualResult:
    adjusted = _adjust(summary, panic_events=0, average_stress=summary.average_stress * 0.7)
    baseline = attribute_lost_time(summary)
    after = attribute_lost_time(adjusted)
    return CounterfactualResult(
        scenario="stable_emotional_state",
        baseline_lap_time_s=baseline.actual_lap_time_s,
        counterfactual_lap_time_s=after.ghost_lap_time_s,
        lap_delta_s=round(after.ghost_lap_time_s - baseline.actual_lap_time_s, 3),
        rationale="Removing panic events and trimming stress recovers most of the lost time on noisy laps.",
        adjustments={"panic_events": 0, "stress_multiplier": 0.7},
    )


def _delayed_rain_onset(summary: LapCognitiveSummary) -> CounterfactualResult:
    adjusted = _adjust(summary, average_stress=summary.average_stress * 0.75)
    baseline = attribute_lost_time(summary)
    after = attribute_lost_time(adjusted)
    return CounterfactualResult(
        scenario="delayed_rain_onset",
        baseline_lap_time_s=baseline.actual_lap_time_s,
        counterfactual_lap_time_s=after.ghost_lap_time_s,
        lap_delta_s=round(after.ghost_lap_time_s - baseline.actual_lap_time_s, 3),
        rationale="Delayed rain reduces wet pressure on the driver and lowers stress driven lost time.",
        adjustments={"stress_multiplier": 0.75},
    )


def _reduced_pressure(summary: LapCognitiveSummary) -> CounterfactualResult:
    adjusted = _adjust(
        summary,
        average_stress=summary.average_stress * 0.65,
        panic_events=max(summary.panic_events - 1, 0),
    )
    baseline = attribute_lost_time(summary)
    after = attribute_lost_time(adjusted)
    return CounterfactualResult(
        scenario="reduced_pressure_environment",
        baseline_lap_time_s=baseline.actual_lap_time_s,
        counterfactual_lap_time_s=after.ghost_lap_time_s,
        lap_delta_s=round(after.ghost_lap_time_s - baseline.actual_lap_time_s, 3),
        rationale="A clearer race situation reduces stress and removes one panic event from the lap.",
        adjustments={"stress_multiplier": 0.65, "panic_events_delta": -1},
    )


_RUNNERS: Dict[str, Callable[[LapCognitiveSummary], CounterfactualResult]] = {
    "earlier_pit_stop": _earlier_pit_stop,
    "lower_fatigue": _lower_fatigue,
    "stable_emotional_state": _stable_emotional_state,
    "delayed_rain_onset": _delayed_rain_onset,
    "reduced_pressure_environment": _reduced_pressure,
}


def run_scenario(scenario: str, summary: LapCognitiveSummary) -> CounterfactualResult:
    if scenario not in _RUNNERS:
        raise ValueError(f"Unknown scenario {scenario!r}. Allowed: {sorted(_RUNNERS)}")
    return _RUNNERS[scenario](summary)


def run_all(summary: LapCognitiveSummary) -> List[CounterfactualResult]:
    return [run_scenario(name, summary) for name in SCENARIOS]
