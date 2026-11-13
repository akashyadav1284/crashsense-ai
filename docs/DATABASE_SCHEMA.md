# CRASHSENSE AI - Database Schema Documentation

MongoDB Atlas serves as the persistence engine for telemetry, model outputs, bankroll guardrails, and audit logs.

## Target Collections & Planned Index Strategy

### 1. `users`
Represents registered users, authentication claims, tier entitlements, and risk profiles.
- **Indexes**:
  - `{ "external_id": 1 }` (unique)
  - `{ "email": 1 }` (unique)
  - `{ "created_at": -1 }`

### 2. `platforms`
Monitored crash game platforms / telemetry providers (e.g., 1xBet, Spribe, BC.Game).
- **Indexes**:
  - `{ "platform_code": 1 }` (unique)
  - `{ "status": 1 }`

### 3. `game_rounds`
Raw and canonical round multiplier records.
- **Fields**: `platform_id`, `round_id`, `crash_multiplier`, `hash_seed`, `started_at`, `crashed_at`
- **Indexes**:
  - `{ "platform_id": 1, "round_id": 1 }` (compound unique)
  - `{ "platform_id": 1, "crashed_at": -1 }`
  - `{ "crash_multiplier": 1 }`

### 4. `model_predictions`
Predicted multiplier distributions and safety thresholds prior to round start.
- **Fields**: `platform_id`, `round_id`, `model_version`, `predicted_multiplier`, `confidence_interval`, `risk_score`, `generated_at`
- **Indexes**:
  - `{ "round_id": 1, "model_version": 1 }` (compound)
  - `{ "generated_at": -1 }`

### 5. `model_versions`
Metadata and lineage for deployed machine learning weights and hyperparameters.
- **Indexes**:
  - `{ "version": 1 }` (unique)
  - `{ "deployed_at": -1 }`

### 6. `prediction_results`
Post-round validation records comparing predicted values against actual crash multipliers.
- **Indexes**:
  - `{ "prediction_id": 1 }` (unique)
  - `{ "error_delta": 1 }`

### 7. `paper_bets`
Simulated dry-run betting execution logs to validate risk engine algorithms without capital risk.
- **Indexes**:
  - `{ "user_id": 1, "created_at": -1 }`
  - `{ "round_id": 1 }`

### 8. `risk_events`
Bankroll safety violations, drawdown alerts, and circuit-breaker triggers.
- **Indexes**:
  - `{ "user_id": 1, "severity": 1, "timestamp": -1 }`

### 9. `audit_logs`
Immutable compliance and security access logs.
- **Indexes**:
  - `{ "timestamp": -1 }`
  - `{ "action": 1, "actor_id": 1 }`

