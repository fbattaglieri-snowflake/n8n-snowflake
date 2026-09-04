# Backup and Recovery

Backup is **opt-in**. Enable it only when you need it — all backup operations are billable.

## What to back up

| Component | Where it lives | Backup method |
|---|---|---|
| **Workflows and credentials** | Snowflake Postgres | Postgres point-in-time recovery (PITR) or fork |
| **n8n block volume** | SPCS block storage | Volume snapshot before high-risk changes |
| **Cortex proxy configuration** | Image + `N8N_CONFIG` stage | Already versioned in Git and staged at deploy time |
| **Snowflake objects** (database, secrets, EAI) | Snowflake metadata | Re-created by `10_bootstrap.sql` |

## Snowflake Postgres

Snowflake Postgres provides automatic point-in-time recovery. To create a fork (read-only clone) for testing:

```sql
-- Replace placeholders with your values
CREATE POSTGRES INSTANCE <FORK_INSTANCE>
  FROM INSTANCE <POSTGRES_INSTANCE>
  AT(TIMESTAMP => '<ISO-8601 timestamp>');
```

Drop the fork when done to avoid ongoing charges.

## Block Volume Snapshot

Before destructive operations (DROP SERVICE, major upgrades):

```sql
-- Manual snapshot — verify the syntax against current Snowflake docs
-- as block volume snapshot support may vary by region
SELECT SYSTEM$SNAPSHOT_BLOCK_VOLUME('<DATABASE>.<SCHEMA>.<SERVICE>', 0);
```

**Important**: `DROP SERVICE` detaches or deletes the block volume. Never drop a service unless you have confirmed the volume is backed up or expendable.

## Workflow Export (optional)

The **Backup** workflow (`.github/workflows/backup.yml`) exports all n8n workflows as JSON to a Snowflake internal stage. Enable it by:

1. Setting the `ENABLE_BACKUP` variable to `true` in your GitHub repository settings.
2. Optionally uncommenting the `schedule` trigger in the workflow file.

Exported workflows land in `@<DATABASE>.<SCHEMA>.N8N_BACKUPS/workflows/`. They do **not** include credentials — credentials live in Postgres and are encrypted with `N8N_ENCRYPTION_KEY`.

## Recovery Scenarios

| Scenario | Recovery |
|---|---|
| Service crash / restart | Automatic: compute pool auto-resumes, Postgres reconnects |
| Postgres data loss | Fork from PITR, re-point n8n at the fork, validate, swap |
| Block volume lost (DROP SERVICE) | Restore from snapshot if available; otherwise redeploy — workflows survive in Postgres |
| Full environment rebuild | Re-run bootstrap + deploy workflows, Postgres PITR restores workflow data |

## What is NOT backed up

- **n8n execution history** beyond Postgres retention — this is ephemeral by design.
- **External integrations** (webhook URLs, OAuth tokens in third-party systems) — these must be reconfigured manually.
