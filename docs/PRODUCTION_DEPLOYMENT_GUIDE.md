# CRASHSENSE AI — PRODUCTION DEPLOYMENT GUIDE

This guide provides end-to-end instructions for deploying CrashSense AI into a production environment using Docker, AWS, Render, or Vercel.

---

## 1. Containerized Deployment (Docker & Docker Compose)

The repository includes a production multi-container setup running FastAPI backend, Next.js frontend, Redis cache, and MongoDB.

### Step 1: Clone and Configure Environment
```bash
git clone https://github.com/crashsense-ai/crashsense.git
cd crashsense
cp .env.example .env.production
# Edit .env.production with production database secrets and secret keys
```

### Step 2: Build and Launch Containers
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Step 3: Verify Container Health
```bash
docker compose -f docker-compose.prod.yml ps
curl -f http://localhost:8000/api/v1/health
```

---

## 2. Cloud Architecture Options

### Architecture A: Modern Serverless / Managed SaaS (Recommended)
- **Frontend:** Deployed to **Vercel** with global edge CDN caching.
  - Set Environment Variables: `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL`.
- **Backend:** Deployed to **AWS ECS / Fargate** or **Render Web Service**.
  - Behind an Application Load Balancer with SSL Termination (TLS 1.3).
  - Minimum 2 replicas for high availability.
- **Database:** **MongoDB Atlas** M10+ replica set with automated daily backups.
- **Cache & Pub/Sub:** **AWS ElastiCache Redis** or **Upstash Redis**.

---

## 3. Production Readiness Checklist

Before switching DNS to live traffic, verify the following:

- [x] Backend test suite passes 100% (`python -m pytest backend/tests -v`).
- [x] Frontend builds with 0 TypeScript/ESLint errors (`npm --prefix frontend run build`).
- [x] End-to-End integration tests pass (`test_e2e.py`).
- [x] `DEBUG` is set to `false`.
- [x] Secret keys (`SECRET_KEY`) are high-entropy, 64-character random strings.
- [x] CORS origins are strictly bound to production domains (`https://app.crashsense.ai`).
- [x] MongoDB compound indexes are created on `game_rounds`, `simulations`, and `notifications`.
- [x] SSL/TLS certificates are active on custom domains.
- [x] Research disclaimers are visible on all ML and prediction views.

