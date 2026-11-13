# CRASHSENSE AI - Data Export Guide

## 1. Export Capabilities
CrashSense AI supports streaming data exports across formats:
1. **CSV Export**: `GET /api/v1/datasets/{dataset_id}/export/csv`
   - Returns streaming `text/csv` response with canonical headers: `round_id, platform_id, provider_id, game_id, room_id, multiplier, round_timestamp, verification_status, source_type`.
2. **JSON Export**: `GET /api/v1/datasets/{dataset_id}/export/json`
   - Returns structured `application/json` array including full provenance objects and cryptographic seeds.

Exports preserve raw source provenance and never leak database connection credentials.
