"""
Live Round Tracker & Operational State Machine.
Tracks live round states: WAITING -> STARTED -> ACTIVE -> COMPLETED / FAILED.
Stores actual final multipliers strictly after an authorized event is verified.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from backend.app.realtime.schemas import (
    LiveRoundRecord,
    RoundLifecycleStatus,
    RealtimeRawEvent,
)
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.connectors.manager import connector_manager


class LiveRoundTracker:
    """Maintains active rounds and state machines across platform/provider/room partitions."""

    _instance: Optional["LiveRoundTracker"] = None

    def __init__(self):
        self.active_rounds: Dict[str, LiveRoundRecord] = {}  # key: round_id or partition::round_id
        self.completed_rounds: List[LiveRoundRecord] = []
        self.max_completed_buffer = 1000

    @classmethod
    def get_instance(cls) -> "LiveRoundTracker":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def process_round_event(self, event: RealtimeRawEvent) -> LiveRoundRecord:
        """Update or register a round's state based on an incoming validated raw event."""
        round_id = event.round_id or f"rnd_{int(event.timestamp.timestamp())}"
        key = f"{event.platform_id}::{event.provider_id}::{event.game_id}::{event.room_id}::{round_id}"

        now = datetime.now(timezone.utc)
        record = self.active_rounds.get(key)

        if not record:
            record = LiveRoundRecord(
                round_id=round_id,
                platform_id=event.platform_id,
                provider_id=event.provider_id,
                game_id=event.game_id,
                room_id=event.room_id,
                status=RoundLifecycleStatus.WAITING,
                source_identity=event.source_identity,
                verification_status="VERIFIED" if event.source_identity != "unknown" else "UNVERIFIED",
                event_received_timestamp=event.timestamp,
                event_processed_timestamp=now,
                data_freshness_ms=round((now - event.timestamp).total_seconds() * 1000.0, 2)
            )
            self.active_rounds[key] = record

        # Transition lifecycle
        if event.event_type == "round_started":
            record.status = RoundLifecycleStatus.STARTED
            record.start_timestamp = event.timestamp
        elif event.event_type == "round_updated":
            record.status = RoundLifecycleStatus.ACTIVE
        elif event.event_type == "round_completed":
            record.status = RoundLifecycleStatus.COMPLETED
            record.completion_timestamp = event.timestamp
            if event.multiplier is not None:
                record.actual_multiplier = float(event.multiplier)

            # Move to completed buffer
            self.completed_rounds.insert(0, record)
            if len(self.completed_rounds) > self.max_completed_buffer:
                self.completed_rounds.pop()
        elif event.event_type == "round_failed":
            record.status = RoundLifecycleStatus.FAILED
            record.completion_timestamp = event.timestamp

        record.event_processed_timestamp = now
        record.data_freshness_ms = max(0.0, round((now - event.timestamp).total_seconds() * 1000.0, 2))
        return record

    def list_live_rounds(
        self,
        platform_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        limit: int = 50
    ) -> List[LiveRoundRecord]:
        """List active and recently completed live rounds."""
        results = list(self.active_rounds.values())
        if platform_id:
            results = [r for r in results if r.platform_id == platform_id]
        if provider_id:
            results = [r for r in results if r.provider_id == provider_id]

        # Combine with recent completed rounds
        combined = results + self.completed_rounds
        # Deduplicate by round_id
        seen = set()
        deduped = []
        for r in combined:
            if r.round_id not in seen:
                seen.add(r.round_id)
                deduped.append(r)
            if len(deduped) >= limit:
                break
        return deduped

    def get_round(self, round_id: str) -> Optional[LiveRoundRecord]:
        for r in self.active_rounds.values():
            if r.round_id == round_id:
                return r
        for r in self.completed_rounds:
            if r.round_id == round_id:
                return r
        return None

