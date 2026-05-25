"""Persona drift state machine.

Maps continuous cognitive scores to one of six discrete labels described in
`docs/COGNITIVE_METHODOLOGY.md`. The rules are evaluated in order and the
first match wins.

When called with a `driver_id`, the classifier shifts the thresholds by the
per driver prior loaded from `data/persona_priors.json` (see
`src/backend/common/priors.py`). Drivers without a prior fall back to the
population defaults, so the legacy signature `classify(stress, confidence,
fatigue, panic_oscillation, throttle_commitment)` keeps working unchanged.
"""

from __future__ import annotations

from typing import Optional

from src.backend.common import priors
from src.backend.common.weights import PERSONA


def classify(
    stress: float,
    confidence: float,
    fatigue: float,
    panic_oscillation: float,
    throttle_commitment: float,
    driver_id: Optional[str] = None,
) -> str:
    thresholds = priors.driver_thresholds(driver_id, PERSONA) if driver_id else PERSONA

    if stress > thresholds.panic_stress and panic_oscillation > thresholds.panic_oscillation:
        return "Panic"
    if stress > thresholds.aggressive_stress and throttle_commitment > thresholds.aggressive_throttle:
        return "Aggressive"
    if fatigue > thresholds.fatigue_score and confidence < thresholds.fatigue_confidence:
        return "Fatigue"
    if confidence < thresholds.defensive_confidence:
        return "Defensive"
    if stress < thresholds.flow_stress and confidence > thresholds.flow_confidence:
        return "Flow State"
    return "Recovery"
