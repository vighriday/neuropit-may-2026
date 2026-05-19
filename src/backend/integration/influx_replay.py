"""Telemetry replay from InfluxDB back into the raw telemetry topic.

The PRD asks for reliable replay so a broker outage does not cost data. The
InfluxDB writer already persists every raw frame. This module reads those
frames back and republishes them on the raw telemetry topic so the rest of
the pipeline reprocesses them from scratch.

Usage:

    python -m src.backend.integration.influx_replay \
        --session 2021_AbuDhabi --driver VER --speed 1.0
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from confluent_kafka import Producer
from influxdb_client import InfluxDBClient

from src.backend.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _build_query(session_id: Optional[str], driver_id: Optional[str], hours: int) -> str:
    settings = get_settings()
    range_window = f"-{max(hours, 1)}h"
    filters = ['r._measurement == "raw_telemetry"']
    if session_id:
        filters.append(f'r.session_id == "{session_id}"')
    if driver_id:
        filters.append(f'r.driver_id == "{driver_id}"')
    filter_block = " and ".join(filters)
    return (
        f'from(bucket: "{settings.influxdb_bucket}") '
        f'|> range(start: {range_window}) '
        f'|> filter(fn: (r) => {filter_block}) '
        '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'
    )


def _row_to_frame(row, driver_id_tag: str, session_id_tag: str) -> dict:
    return {
        "timestamp": row.get_time().isoformat() if hasattr(row.get_time(), "isoformat") else datetime.now(timezone.utc).isoformat(),
        "driver_id": row.values.get("driver_id", driver_id_tag),
        "session_id": row.values.get("session_id", session_id_tag),
        "speed": float(row.values.get("speed", 0.0) or 0.0),
        "rpm": int(row.values.get("rpm", 0) or 0),
        "gear": int(row.values.get("gear", 0) or 0),
        "throttle": float(row.values.get("throttle", 0.0) or 0.0),
        "brake": float(row.values.get("brake", 0.0) or 0.0),
        "steering_angle": float(row.values.get("steering_angle", 0.0) or 0.0),
        "drs": 0,
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "status": "Replay",
    }


def replay(
    session_id: Optional[str] = None,
    driver_id: Optional[str] = None,
    hours: int = 6,
    speed: float = 1.0,
) -> int:
    """Stream historical raw telemetry from InfluxDB onto the raw topic.

    Returns the number of frames that were published.
    """
    settings = get_settings()
    producer = Producer({"bootstrap.servers": settings.kafka_broker_url})
    client = InfluxDBClient(url=settings.influxdb_url, token=settings.influxdb_token, org=settings.influxdb_org)
    query_api = client.query_api()

    query = _build_query(session_id, driver_id, hours)
    logger.info("Replay query: %s", query)

    published = 0
    try:
        tables = query_api.query(query)
        previous_time = None
        for table in tables:
            for record in table.records:
                frame = _row_to_frame(record, driver_id or "VER", session_id or "replay")
                producer.produce(
                    "incoming-telemetry-raw",
                    key=frame["driver_id"].encode("utf-8"),
                    value=json.dumps(frame).encode("utf-8"),
                )
                published += 1

                if speed > 0.0 and previous_time is not None:
                    delta = record.get_time() - previous_time
                    if isinstance(delta, timedelta):
                        seconds = max(delta.total_seconds(), 0.0) / speed
                        if seconds > 0.0:
                            time.sleep(min(seconds, 1.0))
                previous_time = record.get_time()

                if published % 500 == 0:
                    producer.poll(0)
                    logger.info("Replayed %d frames", published)
    finally:
        producer.flush()
        client.close()

    logger.info("Replay complete. %d frames republished.", published)
    return published


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Replay raw telemetry from InfluxDB onto Kafka")
    parser.add_argument("--session", default=None)
    parser.add_argument("--driver", default=None)
    parser.add_argument("--hours", type=int, default=6)
    parser.add_argument("--speed", type=float, default=1.0)
    args = parser.parse_args(argv)

    return 0 if replay(args.session, args.driver, args.hours, args.speed) >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
