# CRASHSENSE AI — PRODUCTION CONFIGURATION GUIDE

This document details the configuration parameters required to run CrashSense AI across Staging and Production environments.

---

## 1. Environment Variables Overview

Environment configuration is managed via Pydantic Settings in `backend/app/core/config.py`.

### Required Environment Variables

```bash
# Application Environment
ENVIRONMENT=production                 # options: development, staging, production
PROJECT_NAME="CrashSense AI"
API_V1_STR="/api/v1"
DEBUG=false

# Security & Authentication
SECRET_KEY="<GENERATE_64_CHAR_HEX_SECRET>"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440        # 24 hours
ALLOWED_HOSTS=["api.crashsense.ai", "localhost"]
CORS_ORIGINS=["https://app.crashsense.ai", "https://dashboard.crashsense.ai"]

# MongoDB Production Connection (Atlas / Replica Set)
MONGODB_URL="mongodb+srv://<db_user>:<db_password>@crashsense-prod.mongodb.net/?retryWrites=true&w=majority"
MONGODB_DB_NAME="crashsense_production"
MONGODB_MIN_POOL_SIZE=10
MONGODB_MAX_POOL_SIZE=100

# Redis Connection (Pub/Sub & Alert Deduplication)
REDIS_URL="rediss://:<redis_password>@crashsense-cache.redis.cache.amazonaws.com:6379/0"

# Model Artifact Storage
MODEL_ARTIFACTS_DIR="/var/crashsense/artifacts/models"
DATASET_STORAGE_DIR="/var/crashsense/artifacts/datasets"

# Ingestion & Realtime Limits
MAX_IMPORT_FILE_SIZE_MB=50
MAX_BATCH_INGEST_SIZE=2500
LIVE_ROUND_TIMEOUT_SECONDS=60
ALERT_DEFAULT_COOLDOWN_SECONDS=60
```

---

## 2. Frontend Configuration (`frontend/.env.production`)

```bash
NEXT_PUBLIC_APP_NAME="CrashSense AI"
NEXT_PUBLIC_API_URL="https://api.crashsense.ai"
NEXT_PUBLIC_WS_URL="wss://api.crashsense.ai/ws"
NEXT_PUBLIC_DEFAULT_PLATFORM="aviator"
NEXT_PUBLIC_ENABLE_SIMULATION_MODE="true"
```

---

## 3. Environment Segregation Matrix

| Configuration Attribute | Development / Staging | Production |
| :--- | :--- | :--- |
| `DEBUG` | `true` | `false` |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Explicit DNS whitelists only |
| Database Engine | Local MongoDB or embedded fallback | MongoDB Atlas Multi-AZ Replica Set |
| Caching & PubSub | In-memory fallback / Redis dev instance | AWS ElastiCache / Redis Cluster with TLS |
| Logging Level | `DEBUG` (human readable) | `INFO` / `WARNING` (JSON structured) |
| Worker Scaling | 1 Uvicorn process | Multi-worker Uvicorn / Gunicorn with Gevent or Uvicorn workers |
| TLS / SSL | Self-signed / None (local) | TLS 1.3 Strict HTTPS / WSS via Cloudflare/ALB |

---

## 4. Production Health Verification

Upon setting the environment variables and launching the container, verify configuration integrity via:
```bash
curl -f https://api.crashsense.ai/api/v1/health
```
Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "cache": "connected",
  "timestamp": "2026-11-13T15:00:00Z"
}
```

