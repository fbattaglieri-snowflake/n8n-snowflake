# Configuration

## Repository Variables

Configure these as GitHub **repository variables**, not secrets:

| Variable | Example | Purpose |
|---|---|---|
| `SNOWFLAKE_ACCOUNT` | `org-account` | Snowflake account identifier used by the CLI. |
| `SNOWFLAKE_DATABASE` | `N8N_PLATFORM` | Deployment database. |
| `SNOWFLAKE_SCHEMA` | `CORE` | Deployment schema. |
| `SNOWFLAKE_BOOTSTRAP_USER` | `N8N_GITHUB_BOOTSTRAP` | OIDC bootstrap service user. |
| `SNOWFLAKE_DEPLOY_USER` | `N8N_GITHUB_DEPLOY` | OIDC production deploy service user. |
| `SNOWFLAKE_BOOTSTRAP_ROLE` | `N8N_GITHUB_BOOTSTRAP_ROLE` | Bootstrap role. |
| `SNOWFLAKE_DEPLOY_ROLE` | `N8N_GITHUB_DEPLOY_ROLE` | Production deploy role. |
| `SNOWFLAKE_WAREHOUSE` | `N8N_DEPLOY_WH` | Small warehouse for deployment SQL. |
| `N8N_COMPUTE_POOL` | `N8N_COMPUTE_POOL` | SPCS compute pool name. |
| `N8N_INSTANCE_FAMILY` | `CPU_X64_M` | Compute pool instance family. |
| `POSTGRES_INSTANCE` | `N8N_POSTGRES` | Snowflake Postgres instance name. |
| `POSTGRES_COMPUTE_FAMILY` | `BURST_S` | Postgres compute family. |
| `POSTGRES_STORAGE_GB` | `20` | Postgres storage allocation. |
| `POSTGRES_INGRESS_CIDR` | `10.0.0.0/16` | Allowed Postgres ingress CIDR. |
| `N8N_IMAGE_REPOSITORY` | `N8N_IMAGES` | n8n image repository. |
| `CORTEX_PROXY_IMAGE_REPOSITORY` | `CORTEX_PROXY_IMAGES` | Proxy image repository. |
| `N8N_VERSION` | `2.34.5` | Explicit upstream n8n release. |

## GitHub Secrets

None are required for Snowflake authentication. The official Snowflake GitHub Action obtains a short-lived OIDC token.

Do not add Postgres passwords, Snowflake private keys, Snowflake PATs, or the n8n encryption key to GitHub.

## GitHub Environments

Create `bootstrap` and `production` environments. Configure `@fbattaglieri-snowflake` as the only required reviewer. Disable administrator bypass if your GitHub plan supports it and you want approvals to be mandatory even for administrators.

## Egress Policy

The default infrastructure permits outbound HTTP and HTTPS because n8n is an integration platform. For a production installation, replace the wildcard rule with explicit destination rules for the services used by your workflows.

