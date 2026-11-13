# CRASHSENSE AI — DATABASE OPERATIONS & INDEXING MANUAL

This document covers MongoDB collection architecture, index definitions, data retention policies, and maintenance procedures.

---

## 1. Production Collections & Schemas

| Collection Name | Purpose | Expected Growth Rate |
| :--- | :--- | :--- |
| `game_rounds` | Normalized historical and live round results | High (~100k - 1M / month) |
| `datasets` | Grouped datasets of validated rounds with metrics | Low (~1k / year) |
| `ml_models` | Trained model metadata, metrics, and parameters | Low (~500 / month) |
| `ml_predictions` | Real-time research estimates and confidence intervals | High (~1M / month) |
| `virtual_bankrolls`| User paper-trading accounts and balance states | Medium (~10k / month) |
| `strategies` | User-defined simulation strategies and parameters | Low (~5k / month) |
| `simulations` | Backtest, replay, and live paper execution logs | Medium (~50k / month) |
| `notifications` | User alerts and system notification events | High (~500k / month) |
| `alert_rules` | User-configured threshold trigger conditions | Medium (~20k / month) |
| `user_profiles` | User account info, preferences, and roles | Medium (~50k / year) |
| `audit_logs` | Immutable security audit trail | High (~200k / month) |

---

## 2. Compound Indexes & Performance Tuning

To support high-throughput ingest and low-latency queries, ensure the following indexes are provisioned:

```javascript
// 1. Game Rounds — Compound Unique & Temporal Queries
db.game_rounds.createIndex(
  { platform_id: 1, round_id: 1 }, 
  { unique: true, name: "idx_platform_round_unique" }
);
db.game_rounds.createIndex(
  { platform_id: 1, timestamp: -1 }, 
  { name: "idx_platform_timestamp_desc" }
);
db.game_rounds.createIndex(
  { dataset_id: 1, timestamp: 1 }, 
  { name: "idx_dataset_timestamp_asc" }
);

// 2. ML Predictions — Prediction Tracking & Scoring
db.ml_predictions.createIndex(
  { platform_id: 1, round_id: 1, model_id: 1 },
  { unique: true, name: "idx_pred_platform_round_model" }
);
db.ml_predictions.createIndex(
  { status: 1, created_at: -1 },
  { name: "idx_pred_status_created" }
);

// 3. Simulations & Paper Trading
db.simulations.createIndex(
  { user_id: 1, created_at: -1 },
  { name: "idx_sim_user_created" }
);
db.virtual_bankrolls.createIndex(
  { user_id: 1, name: 1 },
  { unique: true, name: "idx_bankroll_user_name" }
);

// 4. Notifications & Alerts — TTL and Fast Unread Retrieval
db.notifications.createIndex(
  { user_id: 1, is_read: 1, created_at: -1 },
  { name: "idx_notif_user_unread" }
);
// 30-day Time-To-Live index on notifications
db.notifications.createIndex(
  { created_at: 1 },
  { expireAfterSeconds: 2592000, name: "idx_notif_ttl_30d" }
);

// 5. Security Audit Logs — Immutable Archival
db.audit_logs.createIndex(
  { timestamp: -1, user_id: 1 },
  { name: "idx_audit_timestamp_user" }
);
```

---

## 3. Data Retention & Archival Policies

1. **High-Frequency Telemetry:** Raw uncompleted live round frame buffers are evicted from Redis/Memory after 60 seconds if no crash event is detected.
2. **Notifications:** Cleaned automatically via MongoDB TTL index after 30 days. Read notifications can be bulk purged by users.
3. **Historical Game Rounds:** Stored indefinitely in `game_rounds`. For databases approaching storage thresholds, rounds older than 365 days can be archived to cold S3 Parquet storage via:
   ```bash
   python backend/scripts/archive_historical_rounds.py --before 2025-11-13 --export-s3
   ```
4. **Audit Logs:** Retained for a minimum of 365 days for regulatory and security compliance before cold storage snapshotting.

