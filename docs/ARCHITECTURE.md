# CRASHSENSE AI - Technical Architecture

## 1. System Overview

CRASHSENSE AI is an institutional-grade predictive analytics and telemetry monitoring engine for high-frequency multiplier crash dynamics. The system employs asynchronous pipelines, event-driven websockets, machine learning inference layers, and risk engine guardrails.

```mermaid
graph TB
    subgraph Client Tier
        FE[Next.js 15 Client<br/>React 19 / TypeScript / Tailwind]
    end

    subgraph API & Gateway Tier
        GW[FastAPI Async Gateway<br/>REST & WebSocket Endpoints]
        MW[CORS & Exception Handling]
    end

    subgraph State & In-Memory Tier
        RD[(Redis State Bus<br/>Telemetry PubSub & Session Cache)]
    end

    subgraph Persistence Tier
        MDB[(MongoDB Atlas<br/>Multipliers, Predictions, Audits)]
    end

    subgraph ML & Analytics Engine
        MLE[Inference & Feature Pipelines<br/>Phase 2 / Phase 3 Integration]
    end

    FE <-->|HTTP / REST| GW
    GW --- MW
    GW <-->|Async Event Loop| RD
    GW <-->|Motor Async Driver| MDB
    RD <-->|Pub/Sub Event Bus| MLE
    MLE <-->|Model Predictions| GW
```

---

## 2. Component Responsibilities

### Frontend (`/frontend`)
- **Framework**: Next.js 15 App Router, React 19, TypeScript strict mode.
- **Styling**: Tailwind CSS with custom neon/navy design token system.
- **Role**: Renders telemetry dashboards, real-time odds charts, risk guardrails, and audit logs.
- **Resilience**: Integrated root loading state (`loading.tsx`), graceful error boundary (`error.tsx`), and 404 page (`not-found.tsx`).

### Backend Gateway (`/backend`)
- **Framework**: FastAPI, Python 3.13, Pydantic v2.
- **Role**: Handles telemetry ingestion, authentication, prediction delivery, and system health checks.
- **Concurrency**: Asynchronous non-blocking architecture using `asyncio`, Motor, and `redis.asyncio`.
- **Security**: Strict CORS domain whitelist, non-root container deployment, sanitized diagnostics without credential leaks.

### State & Storage
- **Redis**: High-throughput in-memory pub/sub and ephemeral state cache.
- **MongoDB Atlas**: Sharded document persistence for round telemetry, predictions, and immutable audit logs.

### ML Subsystem (`/ml`)
- Pre-allocated directories for feature engineering, model training, evaluation, and serialized checkpoints in later phases.

