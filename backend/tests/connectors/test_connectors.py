"""Comprehensive Tests for Phase 3 Data Connectors & Ingestion Pipelines."""
import pytest
import io
import json
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.connectors.registry import connector_registry
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.connectors.adapters.csv_import import CSVImportAdapter
from backend.app.connectors.adapters.json_import import JSONImportAdapter
from backend.app.connectors.exceptions import RecordValidationError
from backend.app.connectors.manager import connector_manager


@pytest.mark.asyncio
async def test_connector_registry_mapping():
    """Verify registry resolves adapters and supported types correctly."""
    csv_cls = connector_registry.get_adapter_class("CSV_IMPORT")
    assert csv_cls == CSVImportAdapter

    json_cls = connector_registry.get_adapter_class("JSON_IMPORT")
    assert json_cls == JSONImportAdapter

    supported = connector_registry.list_supported_types()
    assert "OFFICIAL_API" in supported
    assert "CSV_IMPORT" in supported
    assert "JSON_IMPORT" in supported


@pytest.mark.asyncio
async def test_normalized_game_round_validation():
    """Ensure schema strictly rejects non-positive multipliers and empty identifiers."""
    now = datetime.now(timezone.utc)
    # Valid round
    valid = NormalizedGameRound(
        platform_id="1xbet",
        provider_id="spribe",
        game_id="aviator",
        room_id="standard",
        round_id="rnd-101",
        multiplier=2.45,
        round_timestamp=now,
        source_timestamp=now,
        source_type="CSV_IMPORT",
        source_record_id="row-1",
        verification_status="VERIFIED"
    )
    assert valid.multiplier == 2.45
    assert valid.compound_key() == "1xbet::spribe::aviator::standard::rnd-101"

    # Reject multiplier <= 0
    with pytest.raises(ValueError):
        NormalizedGameRound(
            platform_id="1xbet",
            provider_id="spribe",
            game_id="aviator",
            room_id="standard",
            round_id="rnd-102",
            multiplier=-1.0,
            round_timestamp=now,
            source_timestamp=now,
            source_type="CSV_IMPORT",
            source_record_id="row-2"
        )

    # Reject missing round_id
    with pytest.raises(ValueError):
        NormalizedGameRound(
            platform_id="1xbet",
            provider_id="spribe",
            game_id="aviator",
            room_id="standard",
            round_id="",
            multiplier=1.5,
            round_timestamp=now,
            source_timestamp=now,
            source_type="CSV_IMPORT",
            source_record_id="row-3"
        )


@pytest.mark.asyncio
async def test_csv_import_adapter_parsing():
    """Verify CSV adapter normalizes rows with varying column naming."""
    adapter = CSVImportAdapter(connector_id="test_csv", configuration={})
    sample_csv = "round_id,multiplier,timestamp,hash\nround_901,1.85x,2026-11-13T12:00:00Z,seed123\nround_902,3.12,2026-11-13T12:01:00Z,\n"
    rows = adapter.parse_csv_content(sample_csv)
    assert len(rows) == 2

    r1 = adapter.normalize_record(rows[0])
    assert r1.round_id == "round_901"
    assert r1.multiplier == 1.85
    assert r1.verification_status == "VERIFIED"

    r2 = adapter.normalize_record(rows[1])
    assert r2.round_id == "round_902"
    assert r2.multiplier == 3.12
    assert r2.verification_status == "UNVERIFIED"


@pytest.mark.asyncio
async def test_duplicate_detection():
    """Verify duplicate records are detected and counted properly."""
    now = datetime.now(timezone.utc)
    rnd = NormalizedGameRound(
        platform_id="1xbet",
        provider_id="spribe",
        game_id="aviator",
        room_id="standard",
        round_id="dup-check-001",
        multiplier=1.92,
        round_timestamp=now,
        source_timestamp=now,
        source_type="CSV_IMPORT",
        source_record_id="rec-1"
    )

    res1 = await connector_manager.ingest_round(rnd)
    assert res1["status"] in ("ACCEPTED", "DUPLICATE")

    # Ingesting exact same compound key must yield DUPLICATE
    res2 = await connector_manager.ingest_round(rnd)
    assert res2["status"] == "DUPLICATE"


@pytest.mark.asyncio
async def test_api_platforms_endpoints():
    """Verify GET /api/v1/platforms returns declared platforms."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/platforms")
        assert res.status_code == 200
        platforms = res.json()
        assert len(platforms) >= 3
        platform_ids = [p["platform_id"] for p in platforms]
        assert "1xbet" in platform_ids
        assert "bcgame" in platform_ids
        assert "spribe" in platform_ids


@pytest.mark.asyncio
async def test_api_csv_import_pipeline():
    """Verify POST /api/v1/import/csv handles multi-record file ingestion."""
    transport = ASGITransport(app=app)
    csv_data = "round_id,multiplier,timestamp\nimp_01,1.45,2026-11-13T10:00:00Z\nimp_02,2.10,2026-11-13T10:01:00Z\n"
    files = {"file": ("test_rounds.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/import/csv",
            files=files,
            data={"platform_id": "test_platform", "provider_id": "test_provider"}
        )
        assert res.status_code == 200
        job = res.json()
        assert job["total_records"] == 2
        assert job["processed_records"] == 2
        assert job["accepted_records"] >= 0


@pytest.mark.asyncio
async def test_api_rounds_query():
    """Verify GET /api/v1/rounds returns canonical list structure."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/rounds?limit=10")
        assert res.status_code == 200
        data = res.json()
        assert "rounds" in data
        assert "total" in data
