# CRASHSENSE AI — Production Ready Multi-Platform Crash-Game Research SaaS

[![CI/CD Production Validation](https://github.com/crashsense-ai/crashsense/actions/workflows/production-validation.yml/badge.svg)](https://github.com/crashsense-ai/crashsense/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-teal.svg)](https://fastapi.tiangolo.com/)

CrashSense AI is an enterprise-grade analytics, statistical research, machine learning experimentation, real-time monitoring, and paper-trading simulation SaaS platform for crash-style games.

---

## ⚠️ Important Boundary & Research Disclaimer

- **No Real-Money Betting:** CrashSense AI contains no real-money gambling, deposits, withdrawals, or automated betting execution features.
- **No Unauthorized Scraping:** The platform does not bypass CAPTCHAs, reverse-engineer anti-bot protections, or scrape private casino APIs.
- **Research Estimates Only:** Machine learning outputs are research estimates with explicit confidence intervals and Brier score tracking; they are not guarantees of future outcomes.
- **Pure Simulation:** All bankrolls, strategies, backtests, and live paper trades run in isolated virtual environments.

---

## 🌟 10-Phase Capabilities Overview

1. **System Architecture (Phase 1):** Modular FastAPI backend, Pydantic v2 schemas, MongoDB Motor integration, structured health checks.
2. **Premium Dashboard (Phase 2):** Next.js 15 App Router, Tailwind dark cyberpunk aesthetic, Lucide icons, responsive navigation.
3. **Multi-Platform Connectors (Phase 3):** Standardized schema for Aviator, Spaceman, and generic Crash games; CSV batch importer; deduplication.
4. **Historical Data Engine (Phase 4):** 1,000+ round schema, strict data quality rules, monotonicity checks, paginated queries, dataset export.
5. **Statistical Analytics (Phase 5):** Moments (mean, variance, skew, kurtosis), empirical CDF/PDF, Wilson score CI, KS/PSI drift testing, Ljung-Box autocorrelation, IQR outlier detection.
6. **ML Research Laboratory (Phase 6):** Zero-lookahead feature extraction, walk-forward expanding window validation, XGBoost, Random Forest, Logistic Regression, CSPRNG null baseline rejection gates.
7. **Real-Time Monitoring (Phase 7):** Compound deduplication, monotonic sequencing, live round state machine, WebSocket pub/sub telemetry, Brier score outcome matching.
8. **Risk Management & Simulation (Phase 8):** Virtual Bankroll Manager, Strategy Builder (Fixed, Martingale, Kelly), Historical Backtesting, Live Paper Trading, Vectorized Monte Carlo ruin lab, Max Drawdown circuit breakers.
9. **Notifications & RBAC Security (Phase 9):** Centralized notification engine (9 categories, 5 severities), Alert rule engine with cooldowns, User Profile / Preferences, 5-tier RBAC (`USER` to `SUPER_ADMIN`), Security Audit Logging.
10. **Production Readiness (Phase 10):** End-to-End integration test suite (48/48 tests passing), CI/CD GitHub Actions workflow, performance benchmarking (~3,300 req/s), complete operational runbooks.

---

## 🚀 Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- MongoDB (local or Atlas)
- Redis (optional, in-memory fallback enabled)

### Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the dashboard.

---

## 🧪 Testing & Verification

Run the full backend test suite (unit, integration, and E2E):
```bash
python -m pytest backend/tests -v
```

Build the production frontend:
```bash
npm --prefix frontend run build
```

---

## 📚 Complete Project Documentation

- [Final Project Architecture](docs/FINAL_PROJECT_ARCHITECTURE.md)
- [Final Project Audit & System Inventory](docs/FINAL_PROJECT_AUDIT.md)
- [Final Security Audit](docs/FINAL_SECURITY_AUDIT.md)
- [Production Configuration Guide](docs/PRODUCTION_CONFIGURATION.md)
- [Database Operations & Indexing Manual](docs/DATABASE_OPERATIONS.md)
- [Observability, Logging & Monitoring Guide](docs/OBSERVABILITY_GUIDE.md)
- [Backup & Disaster Recovery Runbook](docs/BACKUP_AND_DISASTER_RECOVERY.md)
- [Performance Benchmark Report](docs/PERFORMANCE_BENCHMARK_REPORT.md)
- [Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Final 10-Phase Completion Report](docs/FINAL_COMPLETION_REPORT.md)

---

## 📄 License
Released under the MIT License.
