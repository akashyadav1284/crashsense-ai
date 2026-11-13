# CRASHSENSE AI - Data Quality & Integrity Policy

## 1. Principles of Empirical Ground Truth
- **No Fabricated Records**: Records are stored only when received through validated file uploads or verified network connections.
- **Verification Status Levels**:
  - `VERIFIED`: Provenance includes server seed, client seed, or verifiable cryptographic hash.
  - `UNVERIFIED`: Ingested successfully from a reliable source without hash confirmation.
  - `PENDING`: Ingested into staging buffer awaiting checksum verification.
  - `REJECTED`: Fails structural constraints, non-positive multiplier, or malformed round ID.

---

## 2. Duplicate Detection
MongoDB compound unique index on `(platform_id, provider_id, game_id, room_id, round_id)` prevents overwrites. Re-sent events or repeated API pages generate `DUPLICATE_ROUND_IGNORED` quality events rather than corrupting time-series statistics.
