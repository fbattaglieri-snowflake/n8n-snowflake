# Architecture

## Runtime Components

### n8n Service

The n8n container runs as the non-root `node` user. It stores workflow metadata, credentials, execution history, and webhook state in Snowflake Postgres. A persistent SPCS block volume is mounted at `/home/node/.n8n` for local configuration, community nodes, and temporary files.

The public endpoint is protected by Snowflake ingress. Access requires a Snowflake identity or a valid Snowflake programmatic access token for the endpoint.

### Native Snowflake Node

SPCS writes a short-lived service OAuth token to `/snowflake/session/token` and refreshes it periodically. The image patches n8n's native Snowflake node so each new database connection reads the current token and uses `SNOWFLAKE_HOST`, `SNOWFLAKE_ACCOUNT`, and `authenticator=OAUTH`.

This avoids passwords, key pairs, and PATs inside the n8n container.

### Cortex Proxy

The private proxy solves two separate integration requirements:

- It forwards the Snowflake SQL API using the SPCS service OAuth token.
- It provides an OpenAI-compatible facade for Cortex chat completions used by n8n AI nodes.

The proxy normalizes request and response differences that otherwise break OpenAI-compatible clients: `max_tokens`, empty `finish_reason`, model listing, and tool calling with model-specific reasoning restrictions.

### Snowflake Postgres

Snowflake Postgres provides the durable transactional database required by n8n. The application password is stored as a Snowflake Secret and injected into the n8n service. The repository never writes that password to GitHub logs or files.

### GitHub Actions

GitHub Actions uses two Snowflake service users:

- A bootstrap identity that can create the deployment objects.
- A production identity limited to image publication, staged specifications, service upgrades, and verification.

Each identity trusts only the corresponding protected GitHub environment subject.

## Network Boundaries

- n8n ingress is public but authenticated by Snowflake.
- The Cortex proxy endpoint is private to SPCS.
- Snowflake Postgres accepts only the explicitly configured ingress CIDR.
- n8n internet egress is controlled through an External Access Integration.
- Pull request CI has no Snowflake identity and no deployment permissions.

