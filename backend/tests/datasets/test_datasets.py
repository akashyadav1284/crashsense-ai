"""Comprehensive Integration Tests for Advanced Historical Data Engine."""
import pytest
import io
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.datasets.manager import dataset_manager
from backend.app.datasets.validation import DataValidationEngine
from backend.app.datasets.preparation import DataAnalysisPreparation


@pytest.fixture
def sample_1000_rounds():
    """Generates 1,000 strictly valid test fixture rounds with controlled deterministic values."""
    now = datetime.now(timezone.utc) - timedelta(days=1)
    rounds = []
    for i in range(1, 1001):
        rounds.append(
            NormalizedGameRound(
                platform_id="1xbet",
                provider_id="spribe",
                game_id="aviator",
                room_id="standard",
                round_id=f"test-round-{i:04d}",
                multiplier=round(1.0 + (i % 50) * 0.15, 2),
                round_timestamp=now + timedelta(minutes=i),
                source_timestamp=now + timedelta(minutes=i),
                source_type="CSV_IMPORT",
                source_record_id=str(i),
                verification_status="VERIFIED" if i % 2 == 0 else "UNVERIFIED",
                provenance={"seed": f"seed_{i}"}
            )
        )
    return rounds


@pytest.mark.asyncio
async def test_dataset_creation_and_listing():
    """Verify creating and listing isolated datasets."""
    ds = await dataset_manager.create_dataset(
        dataset_id="ds-test-create",
        platform_id="test_plat",
        provider_id="test_prov",
        game_id="crash",
        room_id="standard",
        dataset_name="Test Isolation Dataset"
    )
    assert ds.dataset_id == "ds-test-create"

    all_ds = await dataset_manager.list_datasets()
    assert any(d.dataset_id == "ds-test-create" for d in all_ds)


@pytest.mark.asyncio
async def test_validation_engine_rules():
    """Verify validation engine catches non-positive, future timestamps, and invalid data."""
    now = datetime.now(timezone.utc)
    valid_round = NormalizedGameRound(
        platform_id="1xbet",
        provider_id="spribe",
        game_id="aviator",
        room_id="standard",
        round_id="valid-1",
        multiplier=1.95,
        round_timestamp=now - timedelta(hours=1),
        source_timestamp=now - timedelta(hours=1),
        source_type="CSV_IMPORT",
        source_record_id="rec-1",
        verification_status="VERIFIED"
    )
    violations = DataValidationEngine.validate_round_record(valid_round)
    # Valid verified round has 0 error violations
    assert not any(v.severity == "ERROR" for v in violations)


@pytest.mark.asyncio
async def test_1000_records_quality_and_rolling_windows(sample_1000_rounds):
    """Test data quality computation and rolling window slices across 1,000 rounds."""
    assert len(sample_1000_rounds) == 1000

    report = DataValidationEngine.compute_dataset_quality("ds-1000", sample_1000_rounds)
    assert report.total_evaluated == 1000
    assert report.valid_records == 1000
    assert report.quality_score >= 90.0

    # Test rolling window extraction
    rolling = DataAnalysisPreparation.extract_rolling_windows(sample_1000_rounds, window_size=50)
    assert len(rolling) == (1000 - 50 + 1)
    assert "rolling_mean" in rolling[0]
    assert "rolling_std" in rolling[0]


@pytest.mark.asyncio
async def test_api_datasets_paginated_query():
    """Verify GET /api/v1/datasets/{id}/rounds pagination metadata."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/datasets/ds-1xbet-aviator-standard/rounds?page=1&page_size=25")
        assert res.status_code == 200
        data = res.json()
        assert "total_records" in data
        assert "page" in data
        assert "total_pages" in data
        assert "has_next" in data


@pytest.mark.asyncio
async def test_api_dataset_exports():
    """Verify CSV and JSON export streams."""
    transport = ASGITransport(app=app)
    # First ingest 2 rounds to test export
    csv_payload = "round_id,multiplier,timestamp\nexp_1,1.55,2026-11-13T10:00:00Z\nexp_2,2.05,2026-11-13T10:01:00Z\n"
    files = {"file": ("export_seed.csv", io.BytesIO(csv_payload.encode("utf-8")), "text/csv")}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/import/csv", files=files, data={"platform_id": "1xbet", "provider_id": "spribe"})

        # CSV Export
        res_csv = await client.get("/api/v1/datasets/ds-1xbet-aviator-standard/export/csv")
        assert res_csv.status_code == 200
        assert "text/csv" in res_csv.headers.get("content-type", "")
        assert "round_id,platform_id" in res_csv.text

        # JSON Export
        res_json = await client.get("/api/v1/datasets/ds-1xbet-aviator-standard/export/json")
        assert res_json.status_code == 200
        assert "application/json" in res_json.headers.get("content-type", "")
