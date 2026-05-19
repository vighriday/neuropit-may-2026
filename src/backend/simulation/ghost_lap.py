"""Ghost Lap AI.

Reconstructs an idealised cognitive normalised lap by subtracting the lost
time attributable to elevated stress, fatigue, and panic from the recorded
lap time. The output is not a magic number. It is an interpretable estimate
that says, in plain language, how much time the driver lost to their own
mental state on a given lap.

The maths is deliberately transparent. Each cognitive contributor has a
documented lost time coefficient and the total lost time per lap is the sum
of those contributions, capped at a reasonable ceiling so a noisy lap does
not produce a silly result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


LOST_TIME_CEILING_S = 3.0


@dataclass(frozen=True)
class LapCognitiveSummary:
    lap_number: int
    driver_id: str
    actual_lap_time_s: float
    average_stress: float
    average_fatigue: float
    panic_events: int


@dataclass(frozen=True)
class GhostLapResult:
    lap_number: int
    driver_id: str
    actual_lap_time_s: float
    ghost_lap_time_s: float
    lost_time_s: float
    contributions: dict


def attribute_lost_time(summary: LapCognitiveSummary) -> GhostLapResult:
    """Compute the cognitive normalised lap and the per cause breakdown."""
    stress_loss = (summary.average_stress / 100.0) * 1.5
    fatigue_loss = (summary.average_fatigue / 100.0) * 0.8
    panic_loss = min(summary.panic_events * 0.25, 1.0)

    total_loss = min(stress_loss + fatigue_loss + panic_loss, LOST_TIME_CEILING_S)
    ghost_time = max(summary.actual_lap_time_s - total_loss, 0.0)

    return GhostLapResult(
        lap_number=summary.lap_number,
        driver_id=summary.driver_id,
        actual_lap_time_s=summary.actual_lap_time_s,
        ghost_lap_time_s=round(ghost_time, 3),
        lost_time_s=round(total_loss, 3),
        contributions={
            "fear_induced_deceleration": round(stress_loss, 3),
            "fatigue_induced_steering_loss": round(fatigue_loss, 3),
            "panic_event_penalty": round(panic_loss, 3),
        },
    )


def attribute_lap_series(summaries: Iterable[LapCognitiveSummary]) -> List[GhostLapResult]:
    return [attribute_lost_time(s) for s in summaries]
