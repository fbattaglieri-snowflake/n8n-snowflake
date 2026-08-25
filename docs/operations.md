# Operations

## Upgrade

Run the **Deploy to Snowflake** workflow with an explicit n8n version. The workflow builds immutable images tagged with the Git commit SHA, pushes them to Snowflake, stages service specifications, and upgrades services with `ALTER SERVICE`.

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

Create a block-volume snapshot before high-risk changes. Use Snowflake Postgres point-in-time recovery or a fork for database recovery testing. Backup and recovery actions are deliberately manual because they are billable and environment-specific.

