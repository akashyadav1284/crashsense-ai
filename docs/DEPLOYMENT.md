# CRASHSENSE AI - Deployment Guide

## 1. Prerequisites
- Node.js >= 20.x
- Python >= 3.11 (3.13 recommended)
- Docker & Docker Compose
- MongoDB Atlas cluster account (or local MongoDB 6+)
- Redis 7+

---

## 2. Local Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Configure credentials in `.env`:
   ```ini
   MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DATABASE=crashsense
   REDIS_URL=redis://localhost:6379/0
   ```

---

## 3. Running with Docker Compose (Recommended)

Run the full stack (Frontend, Backend, Redis) with health checks:
```bash
docker compose up --build -d
```

Verify service states:
```bash
docker compose ps
```

Stop services:
```bash
docker compose down
```

---

## 4. Running Standalone Services Locally

### Backend (FastAPI):
```bash
cd backend
pip install -r requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (Next.js):
```bash
cd frontend
npm install
npm run dev
```
Access frontend at `http://localhost:3000`.

