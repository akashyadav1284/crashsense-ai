"""API integration tests for screenshot analysis endpoints."""
import pytest
import io
from PIL import Image, ImageDraw
from httpx import AsyncClient, ASGITransport

from backend.app.main import create_application


def make_dummy_png():
    img = Image.new("RGB", (300, 100), color=(15, 23, 42))
    d = ImageDraw.Draw(img)
    d.text((20, 30), "1.25x  3.40x  1.05x  10.00x", fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_api_screenshot_analysis_flow():
    app = create_application()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload invalid media type -> 400
        bad_res = await client.post(
            "/api/v1/screenshot-analysis/upload",
            files={"file": ("test.txt", b"not an image", "text/plain")},
        )
        assert bad_res.status_code == 400

        # 2. Upload valid image
        png_data = make_dummy_png()
        up_res = await client.post(
            "/api/v1/screenshot-analysis/upload",
            files={"file": ("screenshot.png", png_data, "image/png")},
        )
        assert up_res.status_code == 201
        data = up_res.json()
        analysis_id = data["id"]
        assert analysis_id.startswith("sa_")

        # 3. Add / Correct extracted data
        correct_payload = {
            "records": [
                {"sequence": 1, "multiplier": 1.50, "ocr_confidence": 0.95},
                {"sequence": 2, "multiplier": 2.10, "ocr_confidence": 0.90},
                {"sequence": 3, "multiplier": 5.40, "ocr_confidence": 0.85},
            ]
        }
        cor_res = await client.put(
            f"/api/v1/screenshot-analysis/{analysis_id}/correct-data",
            json=correct_payload,
        )
        assert cor_res.status_code == 200
        assert len(cor_res.json()["extracted_records"]) == 3

        # 4. Confirm data
        conf_res = await client.post(
            f"/api/v1/screenshot-analysis/{analysis_id}/confirm",
            json={"save_to_historical_dataset": False},
        )
        assert conf_res.status_code == 200
        assert conf_res.json()["extraction_status"] == "CONFIRMED"

        # 5. Run analysis
        run_res = await client.post(f"/api/v1/screenshot-analysis/{analysis_id}/analyze")
        assert run_res.status_code == 200
        analysis_out = run_res.json()
        assert analysis_out["analysis_status"] == "COMPLETED"
        assert analysis_out["statistics"]["sample_size"] == 3
        assert analysis_out["research_estimate"]["verdict"] in [
            "NO_RELIABLE_PREDICTIVE_EDGE_DETECTED",
            "VALIDATED_MODEL_ESTIMATE",
        ]

        # 6. Check history
        hist_res = await client.get("/api/v1/screenshot-analysis/history")
        assert hist_res.status_code == 200
        history_list = hist_res.json()
        assert any(item["id"] == analysis_id for item in history_list)

        # 7. Delete analysis
        del_res = await client.delete(f"/api/v1/screenshot-analysis/{analysis_id}")
        assert del_res.status_code == 204
