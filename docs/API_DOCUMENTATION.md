# CRASHSENSE AI - API Documentation

The CrashSense AI backend exposes versioned endpoints under `/api/v1` along with root health diagnostics.

## Base URLs
- Local Development: `http://localhost:8000`
- Swagger UI Documentation: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`

---

## Endpoints

### 1. Root Health Check
- **Route**: `GET /health`
- **Description**: Returns top-level aggregated health status across core components.
- **Response Format**:
```json
{
  "status": "healthy",
  "app_name": "CrashSense AI Backend",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2026-11-13T07:30:00Z",
  "services": {
    "mongodb": {
      "status": "unconfigured",
      "configured": false,
      "database": "crashsense",
      "message": "MONGODB_URI environment variable is missing"
    },
    "redis": {
      "status": "disconnected",
      "configured": true,
      "message": "Redis client is not connected"
    }
  }
}
```

### 2. API v1 Health Check
- **Route**: `GET /api/v1/health`
- **Description**: Verifies API v1 gateway health and dependency states.
- **Response**: Same as `GET /health`.

### 3. System Information
- **Route**: `GET /api/v1/system/info`
- **Description**: Returns environment and subsystem configuration state without exposing secrets or connection URIs.
- **Response Format**:
```json
{
  "app_name": "CrashSense AI Backend",
  "version": "1.0.0",
  "environment": "development",
  "api_prefix": "/api/v1",
  "services": {
    "mongodb": {
      "configured": false,
      "status": "unconfigured",
      "database": "crashsense"
    },
    "redis": {
      "configured": true,
      "status": "disconnected"
    }
  }
}
```

