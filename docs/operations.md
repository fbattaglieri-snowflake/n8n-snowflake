# Operations

## Upgrade

Run the **Deploy to Snowflake** workflow with an explicit n8n version. Images are tagged with commit SHA, run ID and attempt, so rerunning the same commit does not overwrite the previous build. This is not digest enforcement: operators must still prevent manual tag replacement. The workflow pushes images, stages specifications and upgrades services with `ALTER SERVICE`.

Deployment polls all reported containers for READY, failing after a readiness deadline. This verifies container readiness, not an authenticated application or restore smoke test. Deployment and backup require separate operator approval and have not been exercised end to end by the offline repository tests.

Never drop and recreate the n8n service during a routine upgrade. Dropping the service can detach or delete its block volume and changes the ingress URL.

## Suspend

Use the **Operate Stack** workflow with `suspend`. The required order is:

1. Suspend the n8n and proxy services.
2. Suspend the compute pool.
3. Suspend Snowflake Postgres.

## Resume

Use the **Operate Stack** workflow with `resume`. The required order is:

1. Resume Snowflake Postgres and wait until it is ready.
2. Resume the compute pool.
3. Resume the proxy and n8n services.
4. Verify service readiness.

Starting the compute pool before Postgres can cause n8n to crash and restart repeatedly while its database is unavailable.

## Backup

Verify an independent backup before high-risk changes. Confirm the database retention and recovery window before relying on point-in-time recovery.

The optional, manual **Backup Workflows** action exports workflow definitions to an existing private stage. It is not a full database/credential backup and no schedule is configured. See [backup-recovery.md](backup-recovery.md) for prerequisites and restore acceptance criteria.
