# CRASHSENSE AI — BACKUP & DISASTER RECOVERY RUNBOOK

**Target Recovery Time Objective (RTO):** $\le 15$ Minutes  
**Target Recovery Point Objective (RPO):** $\le 5$ Minutes  

---

## 1. Backup Strategy

### MongoDB Atlas Automated Backups
1. **Continuous Cloud Backups:** Atlas continuous point-in-time recovery (PITR) enabled with 1-minute granularity for the preceding 7 days.
2. **Daily Snapshots:** Taken at 02:00 UTC, retained across 30 days.
3. **Monthly Archival:** First snapshot of each month retained for 12 months in cold storage (AWS S3 Glacier).

### ML Model Artifact Backups
- All model weights, pipeline encoders, and metadata saved in `MODEL_ARTIFACTS_DIR` are mirrored continuously to S3 bucket `s3://crashsense-artifacts-prod/models/` with versioning enabled.

---

## 2. Disaster Scenarios & Recovery Procedures

### Scenario A: Accidental Collection Drop or Data Corruption
1. **Freeze Traffic:** Route frontend to maintenance page or pause WebSocket ingest.
2. **Execute Atlas PITR Restore:**
   - Navigate to MongoDB Atlas $\rightarrow$ Clusters $\rightarrow$ Backup $\rightarrow$ Restore.
   - Select Point in Time 2 minutes prior to corruption event.
   - Restore to a temporary recovery cluster `crashsense-recovery`.
3. **Validate & Swap:**
   - Run verification query: `db.game_rounds.countDocuments()`.
   - Update `MONGODB_URL` connection string on backend pods.
   - Resume traffic.

### Scenario B: Cloud Provider Regional Outage (AWS Region Failure)
1. **DNS Failover:** Route53 health checks trigger automated failover of `api.crashsense.ai` to Secondary Region (e.g., `us-west-2` $\rightarrow$ `us-east-1`).
2. **Atlas Multi-Region Failover:** MongoDB Atlas electable replica promoted in secondary region automatically within 5 seconds.
3. **Frontend Re-route:** Vercel edge routes automatically direct API calls to healthy regional backend.

---

## 3. Disaster Recovery Drill Schedule

- **Quarterly:** Test point-in-time database restore to staging cluster.
- **Bi-annually:** Simulate full regional network cutoff and verify graceful fallback.
- **Post-drill:** Document duration and update runbook.

