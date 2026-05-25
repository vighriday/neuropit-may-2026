"""Per driver persona prior loader.

NeuroPit ships with a population level `PersonaThresholds` (in
`src/backend/common/weights.py`). That default works as a sane
baseline but it ignores the fact that every driver has a distinct
operating envelope. A driver who runs at higher throttle and brake
variability is going to look "stressed" on absolute thresholds even
when they are inside their normal envelope. Conversely, a driver who
runs cooler will look "defensive" on the same absolute thresholds
even when they are pushing inside their personal envelope.

This module loads per driver threshold offsets that are computed
from real F1 telemetry by `scripts/compute_persona_priors.py`. The
offsets are added to the population defaults at persona classification
time. If no priors file exists, or the requested driver is missing,
the engine falls back to the population defaults and the system
behaves exactly as if priors had never been introduced. This is
deliberate: the build cannot become dependent on a generated artifact
that might be missing on a fresh clone.

The full mathematical treatment lives in
`docs/COGNITIVE_METHODOLOGY.md` under the "Per driver priors" section.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, replace
from typing import Optional

from src.backend.common.weights import PERSONA, PersonaThresholds

logger = logging.getLogger(__name__)


_DEFAULT_PRIORS_PATH = "data/persona_priors.json"
_lock = threading.Lock()
_cached_priors: Optional[dict] = None
_priors_source: Optional[dict] = None


@dataclass(frozen=True)
class PriorMetadata:
    """Summary record of which prior set is active.

    Held alongside the per driver thresholds so the audit row can
    document which historical telemetry the priors were trained on.
    """

    available: bool
    source: Optional[dict] = None
    driver_count: int = 0
    path: Optional[str] = None


def _resolve_path(path: Optional[str] = None) -> str:
    if path:
        return path
    env_path = os.environ.get("NEUROPIT_PRIORS_PATH")
    if env_path:
        return env_path
    return _DEFAULT_PRIORS_PATH


def load_priors(path: Optional[str] = None) -> PriorMetadata:
    """Load priors from disk and cache them.

    Returns metadata even when no priors are found, so the cognitive
    engine has something concrete to stamp onto the audit log.
    """
    global _cached_priors, _priors_source
    resolved = _resolve_path(path)

    with _lock:
        if not os.path.exists(resolved):
            logger.info(
                "Persona priors file %s not found, using population defaults",
                resolved,
            )
            _cached_priors = {}
            _priors_source = None
            return PriorMetadata(available=False, path=resolved)

        try:
            with open(resolved, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(
                "Failed to read persona priors at %s, falling back to defaults: %s",
                resolved,
                exc,
            )
            _cached_priors = {}
            _priors_source = None
            return PriorMetadata(available=False, path=resolved)

        drivers = payload.get("drivers", {})
        if not isinstance(drivers, dict):
            logger.warning(
                "Persona priors at %s has malformed drivers section, falling back",
                resolved,
            )
            _cached_priors = {}
            _priors_source = None
            return PriorMetadata(available=False, path=resolved)

        _cached_priors = drivers
        _priors_source = payload.get("source")
        logger.info(
            "Loaded persona priors for %d drivers from %s (source=%s)",
            len(drivers),
            resolved,
            _priors_source,
        )
        return PriorMetadata(
            available=True,
            source=_priors_source,
            driver_count=len(drivers),
            path=resolved,
        )


def reset_for_tests() -> None:
    """Test seam: drop the in-memory cache so the next load reads disk."""
    global _cached_priors, _priors_source
    with _lock:
        _cached_priors = None
        _priors_source = None


def driver_thresholds(driver_id: str, base: PersonaThresholds = PERSONA) -> PersonaThresholds:
    """Return a `PersonaThresholds` shifted by the prior for `driver_id`.

    Drivers without a prior return the base unchanged. This is the
    function the persona classifier should call on every event.
    """
    if _cached_priors is None:
        # Lazy load on first call so production code does not need
        # to remember to bootstrap priors at startup. The cognitive
        # engine still calls `load_priors()` explicitly so the
        # metadata can be cached for the audit log.
        load_priors()

    if not _cached_priors:
        return base

    prior = _cached_priors.get(driver_id)
    if not isinstance(prior, dict):
        return base

    panic_off = float(prior.get("panic_stress_offset", 0.0))
    aggressive_off = float(prior.get("aggressive_stress_offset", 0.0))
    defensive_off = float(prior.get("defensive_confidence_offset", 0.0))
    flow_off = float(prior.get("flow_confidence_offset", 0.0))

    return replace(
        base,
        panic_stress=base.panic_stress + panic_off,
        aggressive_stress=base.aggressive_stress + aggressive_off,
        defensive_confidence=base.defensive_confidence + defensive_off,
        flow_confidence=base.flow_confidence + flow_off,
    )


def priors_metadata() -> dict:
    """Return a serialisable record of the active prior set."""
    if _cached_priors is None:
        load_priors()
    return {
        "available": bool(_cached_priors),
        "driver_count": len(_cached_priors or {}),
        "source": _priors_source,
    }
