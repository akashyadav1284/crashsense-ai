"""
Real-time Ingestion Orchestration Service & Operational Health Monitor.
Coordinates EventValidator, Deduplicator, Ordering, RoundTracker, PredictionTracker,
and WebSocket broadcasting.
"""

import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from backend.app.realtime.schemas import (
    RealtimeRawEvent,
    LiveRoundRecord,
    OperationalMetrics,
    ConnectionHealthStatus,
)
from backend.app.realtime.event_ingestion import (
    EventValidator,
    EventDeduplicator,
    EventOrderingEngine,
)
from backend.app.realtime.connection_manager import ConnectionManager
from backend.app.realtime.live_round_tracker import LiveRoundTracker
from backend.app.realtime.prediction_tracker import PredictionTracker
from backend.app.api.websocket import ws_hub
from backend.app.core.logging import logger


class RealtimeEngine:
    """Singleton coordinator powering the real-time event pipeline."""

    _instance: Optional["RealtimeEngine"] = None

    def __init__(self):
        self.validator = EventValidator()
        self.deduplicator = EventDeduplicator()
        self.ordering = EventOrderingEngine()
        self.conn_manager = ConnectionManager.get_instance()
        self.round_tracker = LiveRoundTracker.get_instance()
        self.prediction_tracker = PredictionTracker.get_instance()

        self.metrics = OperationalMetrics()
        self.latencies: List[float] = []

    @classmethod
    def get_instance(cls) -> "RealtimeEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def ingest_event(self, raw_event_dict: Dict[str, Any]) -> Tuple[bool, str, Optional[LiveRoundRecord]]:
        """
        End-to-end ingestion pipeline:
        1. Validates event schema & multiplier ranges.
        2. Discards duplicate events.
        3. Flags out-of-order records.
        4. Updates connector latency & heartbeat.
        5. Updates LiveRound state machine.
        6. If round is completed, matches and scores pending research estimates.
        7. Broadcasts event over WebSocket.
        """
        t0 = time.perf_counter()
        self.metrics.events_received += 1

        # 1. Validation
        is_valid, val_err, event = self.validator.validate_event(raw_event_dict)
        if not is_valid or event is None:
            self.metrics.events_rejected += 1
            return False, f"Validation rejected: {val_err}", None

        # 2. Deduplication
        if self.deduplicator.is_duplicate(event):
            self.metrics.duplicate_events += 1
            return False, "Duplicate event ignored", None

        # 3. Ordering check
        is_in_order = self.ordering.check_ordering(event)
        if not is_in_order:
            self.metrics.out_of_order_events += 1

        # 4. Connector health update
        conn_id = f"conn-{event.platform_id}-{event.game_id}" if event.game_id else f"conn-{event.platform_id}"
        self.conn_manager.record_event_received(conn_id)

        # 5. Process in LiveRound state machine
        round_record = self.round_tracker.process_round_event(event)

        # 6. Outcome Matching if round completed
        if event.event_type == "round_completed" and event.multiplier is not None:
            round_id = event.round_id or round_record.round_id
            scored = self.prediction_tracker.match_and_score_outcome(
                round_id=round_id,
                platform_id=event.platform_id,
                provider_id=event.provider_id,
                actual_multiplier=float(event.multiplier),
                outcome_timestamp=event.timestamp
            )
            self.metrics.scored_outcome_count += len(scored)

            # Broadcast outcome scored event
            for s in scored:
                await ws_hub.broadcast("estimate_scored", s.dict())

        # 7. WebSocket Broadcasting
        broadcast_type = f"round_{round_record.status.value.lower()}"
        await ws_hub.broadcast(broadcast_type, round_record.dict())

        # Update metrics
        t_proc_ms = (time.perf_counter() - t0) * 1000.0
        self.latencies.append(t_proc_ms)
        if len(self.latencies) > 200:
            self.latencies = self.latencies[-200:]

        self.metrics.events_processed += 1
        self.metrics.average_processing_latency_ms = round(sum(self.latencies) / len(self.latencies), 2)
        self.metrics.last_event_timestamp = datetime.now(timezone.utc)

        return True, "Event ingested successfully", round_record

    def get_operational_metrics(self) -> OperationalMetrics:
        """Collect current real-time telemetry metrics."""
        connectors = self.conn_manager.list_connectors()
        self.metrics.active_connectors = len([c for c in connectors if c.status == ConnectionHealthStatus.HEALTHY])
        self.metrics.healthy_connectors = self.metrics.active_connectors
        self.metrics.disconnected_connectors = len([c for c in connectors if c.status == ConnectionHealthStatus.DISCONNECTED])
        self.metrics.websocket_client_count = len(ws_hub.active_connections)
        self.metrics.pending_outcome_count = sum(len(ids) for ids in self.prediction_tracker.pending_by_round.values())
        return self.metrics
