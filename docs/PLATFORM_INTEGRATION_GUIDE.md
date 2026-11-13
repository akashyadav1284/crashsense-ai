# CRASHSENSE AI - Platform Integration Guide

## 1. Betting Platforms & Provider Decoupling
CrashSense AI treats platforms (e.g. 1xBet, BC.Game, Stake) as separate entities from game providers (e.g. Spribe Aviator, Pragmatic Spaceman, In-house Crash).

A single platform may offer several crash games from distinct software providers, each having different round frequencies, seed mechanisms, and house edges. Data from different providers or tables are never pooled or conflated.

---

## 2. Platform Status Declarations

| Platform | Provider | Default Status | Notes |
| :--- | :--- | :--- | :--- |
| **1xBet** | Spribe / In-House | `NOT CONFIGURED` | Awaiting authorized endpoint and credentials. |
| **BC.Game** | BC Originals | `NOT CONFIGURED` | Awaiting authenticated WebSocket token. |
| **Spribe Global** | Spribe Gaming Ltd | `AUTHORIZATION REQUIRED` | Requires licensed aggregator API credentials. |
| **CSV Import** | Offline Archives | `READY` / `CONNECTED` | Full local processing engine available. |
| **JSON Import** | Offline Archives | `READY` / `CONNECTED` | Full local processing engine available. |

---

## 3. Safe Integration Compliance
- No automated player account logins.
- No reverse-engineering of cloudflare-protected endpoints.
- No scraping of anti-bot challenge-protected pages.
- Data ingestion is restricted to official APIs, licensed commercial feeds, authorized WebSockets, and user-supplied data files.
