"""Connector Manager and Data Quality / Deduplication Ingestion Service."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo.errors import DuplicateKeyError
from backend.app.connectors.base import BaseConnector
from backend.app.connectors.registry import connector_registry
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.connectors.schemas.source import PlatformConfig
from backend.app.connectors.schemas.connector import ImportJob, DataQualityEvent, ConnectorHealthStatus
from backend.app.database.mongodb import mongo_manager
from backend.app.core.logging import logger


class ConnectorManager:
    """Orchestrates multi-platform connectors, deduplication, and database persistence."""

    def __init__(self):
        self._active_connectors: Dict[str, BaseConnector] = {}
        # In-memory store fallback when MongoDB Atlas is unconfigured
        self._memory_platforms: Dict[str, PlatformConfig] = {}
        self._memory_rounds: Dict[str, NormalizedGameRound] = {}
        self._memory_import_jobs: Dict[str, ImportJob] = {}
        self._memory_dq_events: List[DataQualityEvent] = []
        self._init_default_platforms()

    def _init_default_platforms(self) -> None:
        """Seed initial platform declarations with NOT CONFIGURED status."""
        defaults = [
            PlatformConfig(
                platform_id="1xbet",
                platform_name="1xBet Crash Multiplier Ingest",
                integration_type="OFFICIAL_API",
                provider_name="Spribe / In-House",
                authorization_status="NOT CONFIGURED",
                connection_status="DISCONNECTED",
                configuration={"note": "API endpoint & credentials required"}
            ),
            PlatformConfig(
                platform_id="bcgame",
                platform_name="BC.Game Crash Telemetry",
                integration_type="AUTHORIZED_WS",
                provider_name="BC Originals",
                authorization_status="NOT CONFIGURED",
                connection_status="DISCONNECTED",
                configuration={"note": "WebSocket JWT token required"}
            ),
            PlatformConfig(
                platform_id="spribe",
                platform_name="Spribe Global Network",
                integration_type="LICENSED_FEED",
                provider_name="Spribe Gaming Ltd",
                authorization_status="AUTHORIZATION REQUIRED",
                connection_status="DISCONNECTED",
                configuration={"note": "Commercial aggregator key required"}
            ),
            PlatformConfig(
                platform_id="csv_import",
                platform_name="Offline CSV Ingestion Engine",
                integration_type="CSV_IMPORT",
                provider_name="Historical Archives",
                authorization_status="AUTHORIZED",
                connection_status="CONNECTED",
                configuration={}
            ),
            PlatformConfig(
                platform_id="json_import",
                platform_name="Offline JSON / NDJSON Ingestion Engine",
                integration_type="JSON_IMPORT",
                provider_name="Historical Archives",
                authorization_status="AUTHORIZED",
                connection_status="CONNECTED",
                configuration={}
            )
        ]
        for p in defaults:
            self._memory_platforms[p.platform_id] = p

    async def initialize_database_indexes(self) -> None:
        """Create compound unique indexes on MongoDB collections."""
        if mongo_manager.database is None:
            logger.info("MongoDB client offline; skipping persistent index creation.")
            return

        try:
            db = mongo_manager.database
            # game_rounds: Compound unique index ensuring absolute deduplication
            await db.game_rounds.create_index(
                [
                    ("platform_id", 1),
                    ("provider_id", 1),
                    ("game_id", 1),
                    ("room_id", 1),
                    ("round_id", 1),
                ],
                unique=True,
                name="idx_compound_unique_round"
            )
            # Secondary query indexes
            await db.game_rounds.create_index([("round_timestamp", -1)], name="idx_round_ts")
            await db.game_rounds.create_index([("multiplier", 1)], name="idx_multiplier")
            await db.import_jobs.create_index([("job_id", 1)], unique=True, name="idx_job_id")
            await db.platforms.create_index([("platform_id", 1)], unique=True, name="idx_platform_id")
            logger.info("Successfully ensured MongoDB indexes for CrashSense AI.")
        except Exception as exc:
            logger.error("Failed to create database indexes: %s", str(exc))

    # --- Platforms ---
    async def list_platforms(self) -> List[PlatformConfig]:
        if mongo_manager.database is not None:
            cursor = mongo_manager.database.platforms.find({}, {"_id": 0})
            docs = await cursor.to_list(length=100)
            if docs:
                return [PlatformConfig(**d) for d in docs]
        return list(self._memory_platforms.values())

    async def get_platform(self, platform_id: str) -> Optional[PlatformConfig]:
        if mongo_manager.database is not None:
            doc = await mongo_manager.database.platforms.find_one({"platform_id": platform_id}, {"_id": 0})
            if doc:
                return PlatformConfig(**doc)
        return self._memory_platforms.get(platform_id)

    async def save_platform(self, config: PlatformConfig) -> PlatformConfig:
        config.updated_at = datetime.now(timezone.utc)
        self._memory_platforms[config.platform_id] = config
        if mongo_manager.database is not None:
            await mongo_manager.database.platforms.update_one(
                {"platform_id": config.platform_id},
                {"$set": config.model_dump()},
                upsert=True
            )
        return config

    # --- Connector Instantiation ---
    def get_or_create_connector(self, platform_id: str) -> BaseConnector:
        if platform_id in self._active_connectors:
            return self._active_connectors[platform_id]

        plat = self._memory_platforms.get(platform_id)
        if not plat:
            raise ValueError(f"Platform '{platform_id}' not found.")

        adapter_cls = connector_registry.get_adapter_class(plat.integration_type)
        instance = adapter_cls(connector_id=platform_id, configuration=plat.configuration)
        self._active_connectors[platform_id] = instance
        return instance

    # --- Ingestion & Deduplication Pipeline ---
    async def ingest_round(self, round_record: NormalizedGameRound) -> Dict[str, Any]:
        """Ingests a single canonical round with strict duplicate detection."""
        key = round_record.compound_key()

        # Database persistence
        if mongo_manager.database is not None:
            try:
                doc = round_record.model_dump()
                await mongo_manager.database.game_rounds.insert_one(doc)
                self._memory_rounds[key] = round_record
                return {"status": "ACCEPTED", "round_id": round_record.round_id, "key": key}
            except DuplicateKeyError:
                # Log duplicate data quality event
                await self.record_data_quality_event(
                    source_id=round_record.platform_id,
                    severity="WARNING",
                    reason="DUPLICATE_ROUND_IGNORED",
                    round_id=round_record.round_id,
                    payload={"compound_key": key}
                )
                return {"status": "DUPLICATE", "round_id": round_record.round_id, "key": key}
            except Exception as exc:
                logger.error("DB error ingesting round: %s", str(exc))
                return {"status": "ERROR", "message": str(exc)}
        else:
            # Memory store path
            if key in self._memory_rounds:
                await self.record_data_quality_event(
                    source_id=round_record.platform_id,
                    severity="WARNING",
                    reason="DUPLICATE_ROUND_IGNORED",
                    round_id=round_record.round_id,
                    payload={"compound_key": key}
                )
                return {"status": "DUPLICATE", "round_id": round_record.round_id, "key": key}

            self._memory_rounds[key] = round_record
            return {"status": "ACCEPTED", "round_id": round_record.round_id, "key": key}

    async def ingest_batch(self, job_id: str, records: List[NormalizedGameRound]) -> ImportJob:
        """Batch ingestion loop tracking duplicates, accepted, and rejected counts."""
        job = self._memory_import_jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        job.status = "PROCESSING"
        for rec in records:
            if job.status == "CANCELLED":
                logger.info("Import job %s was cancelled by user.", job_id)
                break

            job.processed_records += 1
            res = await self.ingest_round(rec)
            if res["status"] == "ACCEPTED":
                job.accepted_records += 1
            elif res["status"] == "DUPLICATE":
                job.duplicate_records += 1
            else:
                job.rejected_records += 1
                job.errors.append(f"Round {rec.round_id}: {res.get('message', 'Rejected')}")

        if job.status != "CANCELLED":
            job.status = "COMPLETED"
        job.completed_at = datetime.now(timezone.utc)
        self._memory_import_jobs[job_id] = job

        if mongo_manager.database is not None:
            await mongo_manager.database.import_jobs.update_one(
                {"job_id": job.job_id},
                {"$set": job.model_dump()},
                upsert=True
            )
        return job

    # --- Data Quality Logging ---
    async def record_data_quality_event(
        self,
        source_id: str,
        severity: str,
        reason: str,
        round_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> DataQualityEvent:
        event = DataQualityEvent(
            event_id=str(uuid.uuid4()),
            round_id=round_id,
            source_id=source_id,
            severity=severity,
            reason=reason,
            payload=payload or {}
        )
        self._memory_dq_events.append(event)
        if mongo_manager.database is not None:
            try:
                await mongo_manager.database.data_quality_events.insert_one(event.model_dump())
            except Exception:
                pass
        return event

    async def list_dq_events(self, limit: int = 50) -> List[DataQualityEvent]:
        if mongo_manager.database is not None:
            cursor = mongo_manager.database.data_quality_events.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
            if docs:
                return [DataQualityEvent(**d) for d in docs]
        return list(reversed(self._memory_dq_events[-limit:]))

    # --- Query Rounds ---
    async def query_rounds(
        self,
        platform_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[NormalizedGameRound]:
        if mongo_manager.database is not None:
            filt: Dict[str, Any] = {}
            if platform_id and platform_id != "all":
                filt["platform_id"] = platform_id
            if provider_id and provider_id != "all":
                filt["provider_id"] = provider_id
            if search:
                filt["$or"] = [
                    {"round_id": {"$regex": search, "$options": "i"}},
                    {"provenance.hash_seed": {"$regex": search, "$options": "i"}}
                ]
            cursor = mongo_manager.database.game_rounds.find(filt, {"_id": 0}).sort("round_timestamp", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
            return [NormalizedGameRound(**d) for d in docs]

        # In-memory query
        all_rounds = list(self._memory_rounds.values())
        filtered = []
        for r in all_rounds:
            if platform_id and platform_id != "all" and r.platform_id != platform_id:
                continue
            if provider_id and provider_id != "all" and r.provider_id != provider_id:
                continue
            if search and search.lower() not in r.round_id.lower():
                continue
            filtered.append(r)
        filtered.sort(key=lambda x: x.round_timestamp, reverse=True)
        return filtered[:limit]


connector_manager = ConnectorManager()
