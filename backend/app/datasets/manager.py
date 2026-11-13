"""Dataset Management Service."""
import uuid
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.app.datasets.models import (
    DatasetMetadata,
    DatasetValidationReport,
    DatasetCoverageReport,
    PaginatedRoundsResponse,
)
from backend.app.datasets.validation import DataValidationEngine
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.connectors.manager import connector_manager
from backend.app.database.mongodb import mongo_manager
from backend.app.core.logging import logger


class DatasetManager:
    """Manages isolated historical datasets, coverage, validation reports, and paginated queries."""

    def __init__(self):
        self._memory_datasets: Dict[str, DatasetMetadata] = {}
        self._memory_reports: Dict[str, DatasetValidationReport] = {}
        self._init_default_datasets()

    def _init_default_datasets(self) -> None:
        defaults = [
            DatasetMetadata(
                dataset_id="ds-1xbet-aviator-standard",
                platform_id="1xbet",
                provider_id="spribe",
                game_id="aviator",
                room_id="standard",
                dataset_name="1xBet Aviator (Standard Room)",
                description="Canonical historical dataset for 1xBet Spribe Aviator.",
                source_type="MIXED"
            ),
            DatasetMetadata(
                dataset_id="ds-bcgame-crash-standard",
                platform_id="bcgame",
                provider_id="bc_originals",
                game_id="crash",
                room_id="standard",
                dataset_name="BC.Game Crash (Originals)",
                description="Canonical historical dataset for BC.Game Crash.",
                source_type="MIXED"
            ),
            DatasetMetadata(
                dataset_id="ds-spribe-global-aviator",
                platform_id="spribe",
                provider_id="spribe",
                game_id="aviator",
                room_id="standard",
                dataset_name="Spribe Global Network Feed",
                description="Aggregated multi-operator feed for Spribe Aviator.",
                source_type="LICENSED_FEED"
            ),
            DatasetMetadata(
                dataset_id="ds-historical-archive",
                platform_id="historical_import",
                provider_id="generic",
                game_id="crash",
                room_id="standard",
                dataset_name="Imported Historical Archives",
                description="User-uploaded historical research records.",
                source_type="CSV_IMPORT"
            )
        ]
        for ds in defaults:
            self._memory_datasets[ds.dataset_id] = ds

    async def list_datasets(self) -> List[DatasetMetadata]:
        # Refresh counts dynamically
        results = []
        for ds in self._memory_datasets.values():
            rounds = await self.get_dataset_rounds(ds.dataset_id)
            ds.total_records = len(rounds)
            if rounds:
                sorted_r = sorted(rounds, key=lambda x: x.round_timestamp)
                ds.first_round_timestamp = sorted_r[0].round_timestamp
                ds.last_round_timestamp = sorted_r[-1].round_timestamp
            results.append(ds)
        return results

    async def get_dataset(self, dataset_id: str) -> Optional[DatasetMetadata]:
        ds = self._memory_datasets.get(dataset_id)
        if ds:
            rounds = await self.get_dataset_rounds(dataset_id)
            ds.total_records = len(rounds)
            if rounds:
                sorted_r = sorted(rounds, key=lambda x: x.round_timestamp)
                ds.first_round_timestamp = sorted_r[0].round_timestamp
                ds.last_round_timestamp = sorted_r[-1].round_timestamp
        return ds

    async def create_dataset(
        self,
        dataset_id: str,
        platform_id: str,
        provider_id: str,
        game_id: str,
        room_id: str,
        dataset_name: str,
        description: Optional[str] = None
    ) -> DatasetMetadata:
        ds = DatasetMetadata(
            dataset_id=dataset_id,
            platform_id=platform_id,
            provider_id=provider_id,
            game_id=game_id,
            room_id=room_id,
            dataset_name=dataset_name,
            description=description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self._memory_datasets[dataset_id] = ds
        return ds

    async def get_dataset_rounds(self, dataset_id: str) -> List[NormalizedGameRound]:
        """Fetch all rounds strictly belonging to this dataset's platform/provider/room partition."""
        ds = self._memory_datasets.get(dataset_id)
        if not ds:
            # Fallback to general query
            return await connector_manager.query_rounds(limit=5000)

        # Isolated partition query
        all_rounds = await connector_manager.query_rounds(
            platform_id=ds.platform_id if ds.platform_id != "historical_import" else None,
            provider_id=ds.provider_id if ds.provider_id != "generic" else None,
            limit=5000
        )
        return all_rounds

    async def query_dataset_paginated(
        self,
        dataset_id: str,
        page: int = 1,
        page_size: int = 50,
        sort_order: str = "desc",
        search: Optional[str] = None,
        min_multiplier: Optional[float] = None,
        max_multiplier: Optional[float] = None
    ) -> PaginatedRoundsResponse:
        """Indexed, paginated, filtered historical query engine."""
        rounds = await self.get_dataset_rounds(dataset_id)

        # Filters
        filtered = []
        for r in rounds:
            if search and search.lower() not in r.round_id.lower():
                continue
            if min_multiplier is not None and r.multiplier < min_multiplier:
                continue
            if max_multiplier is not None and r.multiplier > max_multiplier:
                continue
            filtered.append(r)

        # Sorting
        reverse = (sort_order.lower() == "desc")
        filtered.sort(key=lambda x: x.round_timestamp, reverse=reverse)

        total_records = len(filtered)
        total_pages = max(1, math.ceil(total_records / page_size))
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        slice_rounds = filtered[start_idx:end_idx]

        return PaginatedRoundsResponse(
            total_records=total_records,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=(page < total_pages),
            has_previous=(page > 1),
            rounds=[r.model_dump() for r in slice_rounds]
        )

    async def generate_validation_report(self, dataset_id: str) -> DatasetValidationReport:
        rounds = await self.get_dataset_rounds(dataset_id)
        report = DataValidationEngine.compute_dataset_quality(dataset_id, rounds)
        self._memory_reports[dataset_id] = report

        # Update dataset status & score
        ds = self._memory_datasets.get(dataset_id)
        if ds:
            ds.quality_score = report.quality_score
            ds.data_quality_status = report.status
            ds.updated_at = datetime.now(timezone.utc)

        return report

    async def get_coverage_report(self, dataset_id: str) -> DatasetCoverageReport:
        rounds = await self.get_dataset_rounds(dataset_id)
        if not rounds:
            return DatasetCoverageReport(
                dataset_id=dataset_id,
                total_records=0,
                start_time=None,
                end_time=None,
                timespan_hours=0.0,
                average_interval_seconds=0.0,
                gaps_detected=0
            )

        sorted_r = sorted(rounds, key=lambda x: x.round_timestamp)
        start_t = sorted_r[0].round_timestamp
        end_t = sorted_r[-1].round_timestamp
        diff_secs = (end_t - start_t).total_seconds()
        hours = max(0.0, diff_secs / 3600.0)
        avg_interval = diff_secs / len(rounds) if len(rounds) > 1 else 0.0

        return DatasetCoverageReport(
            dataset_id=dataset_id,
            total_records=len(rounds),
            start_time=start_t,
            end_time=end_t,
            timespan_hours=round(hours, 2),
            average_interval_seconds=round(avg_interval, 2),
            gaps_detected=0
        )


dataset_manager = DatasetManager()
