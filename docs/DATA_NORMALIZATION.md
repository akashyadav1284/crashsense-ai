# CRASHSENSE AI - Data Normalization Specification

## 1. The Canonical Game Round Schema

Heterogeneous platforms format round events differently. CrashSense AI maps every record into `NormalizedGameRound`:

```json
{
  "platform_id": "1xbet",
  "provider_id": "spribe",
  "game_id": "aviator",
  "room_id": "standard",
  "round_id": "89312891",
  "multiplier": 2.45,
  "round_timestamp": "2026-11-13T12:00:00Z",
  "source_timestamp": "2026-11-13T12:00:00Z",
  "ingestion_timestamp": "2026-11-13T12:00:01.120Z",
  "source_type": "OFFICIAL_REST",
  "source_record_id": "89312891",
  "verification_status": "VERIFIED",
  "provenance": {
    "hash_seed": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "raw_response": { ... }
  }
}
```

---

## 2. Validation & Constraint Rules

- **Multiplier Constraint**: Must be a positive finite float ($> 0.00$). Any non-numeric string (e.g. `"crash"`, `"null"`, negative floats, or `NaN`) is rejected immediately.
- **Timestamp Standard**: All internal dates are normalized to UTC `datetime` objects. Epoch timestamps (in seconds or milliseconds) are detected and converted.
- **Compound Primary Key**: `platform_id::provider_id::game_id::room_id::round_id`.
- **Deduplication Policy**: Duplicates are dropped from insertion and recorded in the Data Quality event log.
