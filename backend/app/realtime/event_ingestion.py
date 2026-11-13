"""
Real-time Ingestion, Event Normalization, Deduplication, and Ordering Engine.
Validates live events, discards duplicates using compound keys, flags out-of-order records,
and maintains high-precision telemetry metrics.
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, Set, List
from backend.app.realtime.schemas import (
    RealtimeRawEvent,
    LiveRoundRecord,
    RoundLifecycleStatus,
)
from backend.app.core.logging import logger


class EventValidator:
    """Strictly validates event schema, non-negative multipliers, and source identity."""

    @staticmethod
    def validate_event(event_dict: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[RealtimeRawEvent]]:
        if not isinstance(event_dict, dict):
            return False, "Payload must be a JSON object", None

        # Check required fields
        required = ["event_id", "event_type", "platform_id", "provider_id", "game_id", "room_id", "source_identity"]
        for field in required:
            if not event_dict.get(field):
                return False, f"Missing required event field: '{field}'", None

        # Check multiplier validity if present
        multiplier = event_dict.get("multiplier")
        if multiplier is not None:
            try:
                m_val = float(multiplier)
                if m_val < 1.0:
                    return False, f"Multiplier cannot be less than 1.00x: received {m_val}", None
                event_dict["multiplier"] = m_val
            except (ValueError, TypeError):
                return False, f"Invalid multiplier value: {multiplier}", None

        # Ensure timestamp is parsed properly
        ts = event_dict.get("timestamp")
        if isinstance(ts, str):
            try:
                event_dict["timestamp"] = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                event_dict["timestamp"] = datetime.now(timezone.utc)
        elif not isinstance(ts, datetime):
            event_dict["timestamp"] = datetime.now(timezone.utc)

        try:
            raw_event = RealtimeRawEvent(**event_dict)
            return True, None, raw_event
        except Exception as e:
            return False, f"Event validation error: {str(e)}", None


class EventDeduplicator:
    """In-memory sliding window deduplicator for compound event keys."""

    def __init__(self, max_capacity: int = 10000):
        self.seen_events: Set[str] = set()
        self.max_capacity = max_capacity
        self.ordered_keys: List[str] = []

    def is_duplicate(self, event: RealtimeRawEvent) -> bool:
        # Key on event_id or compound round lifecycle key
        key = f"{event.platform_id}::{event.provider_id}::{event.game_id}::{event.room_id}::{event.event_id}"
        if key in self.seen_events:
            return True

        if len(self.ordered_keys) >= self.max_capacity:
            oldest = self.ordered_keys.pop(0)
            self.seen_events.discard(oldest)

        self.seen_events.add(key)
        self.ordered_keys.append(key)
        return False


class EventOrderingEngine:
    """Detects and flags out-of-order events by tracking sequence timestamps per room partition."""

    def __init__(self):
        self.last_seen_timestamps: Dict[str, datetime] = {}

    def check_ordering(self, event: RealtimeRawEvent) -> bool:
        """Returns True if event is in order (timestamp >= last seen), False if out-of-order."""
        partition = f"{event.platform_id}::{event.provider_id}::{event.game_id}::{event.room_id}"
        last_ts = self.last_seen_timestamps.get(partition)

        if last_ts is not None and event.timestamp < last_ts:
            logger.warning(
                "Out-of-order event detected for %s: current ts=%s < previous ts=%s",
                partition, event.timestamp.isoformat(), last_ts.isoformat()
            )
            return False

        self.last_seen_timestamps[partition] = event.timestamp
        return True

