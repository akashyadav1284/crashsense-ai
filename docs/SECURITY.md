# CRASHSENSE AI - Security Architecture & Policy

## 1. Zero Trust Principles
- **Credential Segregation**: Database URIs, Redis credentials, and authentication secrets are loaded strictly via environment variables. They must never be checked into version control or bundled into client builds.
- **Client Exposure Prevention**: Only variables prefixed with `NEXT_PUBLIC_` are visible in the frontend browser environment. All database connections and third-party API keys are isolated within the backend runtime.

## 2. API Security & CORS Policy
- CORS is configured with an explicit origin allowlist (`CORS_ORIGINS`). Wildcard (`*`) origins are prohibited in production environments.
- Rate limiting and token bucket throttles are scheduled for the API Gateway in Phase 2.

## 3. Container Hardening
- Backend Docker containers execute under a dedicated non-privileged user (`appuser`).
- Frontend Next.js containers run under the unprivileged `nextjs` user.
- Root execution inside Docker containers is strictly avoided.

## 4. Diagnostics & Information Disclosure
- Public health endpoints (`/health`, `/api/v1/system/info`) report service connectivity state (`connected`, `disconnected`, `unconfigured`) but never echo raw database strings, passwords, or cluster hostnames.

