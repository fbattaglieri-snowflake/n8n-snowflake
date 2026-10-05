# Backup and Recovery

## Scope and verification

The optional, manually dispatched GitHub workflow exports workflow definitions
as a JSON array to an existing private Snowflake stage. It is not a full n8n
backup. No account-specific credentials or destinations are shipped in this repo.
Offline tests validate pagination, authentication headers and failure handling;
an end-to-end export/import drill is still required in the operator's environment.

## Workflow export prerequisites

Configure these in the protected `production` environment before dispatch:

| Setting | Purpose |
|---|---|
| Variable `N8N_BACKUP_ENDPOINT` | HTTPS origin of the n8n Snowflake public ingress, without a path |
| Variable `N8N_BACKUP_STAGE` | Existing private internal stage destination, `@DATABASE.SCHEMA.STAGE/workflows/` |
| Secret `N8N_BACKUP_INGRESS_TOKEN` | Operator-managed Snowflake ingress token with access to this service |
| Secret `N8N_BACKUP_API_KEY` | n8n API key with workflow read access |

The existing Snowflake OIDC deployment identity is used only for the stage upload.
Registry authentication is not treated as interchangeable with ingress or n8n
authentication. The operator must provision and rotate the two runtime secrets;
the repository neither creates nor discovers them. Use the least available
privileges and verify expiry before dispatch. Never print tokens in logs.

The stage must already exist and the upload identity must have the required
access. This workflow creates no stage and requires no account-admin role.
For simplicity, stage configuration supports unquoted database/schema/stage
identifiers and a path containing letters, digits, underscores, slashes or hyphens.

The exporter fetches all pages, rejects redirects, duplicate IDs, repeated
cursors, missing node definitions and empty exports. It writes the output only
after every page succeeds. Any failure prevents upload and fails the job.
Exports use a unique run/attempt filename and are removed from the runner at exit.
There is no scheduled trigger; `ENABLE_BACKUP` is no longer used.

## Confidentiality and consistency

Workflow JSON can contain hardcoded credentials, private text and connection
details even though credential records are not exported. Treat it as confidential:
restrict stage access, require encryption, define retention, and never publish
exports as GitHub artifacts or commit them. Coordinate workflow edits during the
export: pagination is not a transactional snapshot of an actively edited system.

## Full recovery requires more than workflow JSON

- Back up the n8n database, including credential records and any required execution
  history, using a supported database backup method with verified retention.
- Preserve `N8N_ENCRYPTION_KEY` securely and independently; the original key is
  required to decrypt restored credentials.
- Include required block-volume files and external integration settings.
- Do not assume PITR is available without checking the configured retention and
  recoverable window. Database forks are not inherently read-only.
- Do not drop a service until its persistent data is backed up or expendable.

## Restore acceptance

Download the export through an authorized private path and import it into an
isolated n8n instance using that version's documented workflow import command.
Keep schedules, webhooks and messaging inactive during the drill. Compare workflow
IDs, node definitions and connections, then validate credential recovery separately.
Record checksum, timestamp, workflow count and restore results. A successful upload
alone is not a successful restore. The repository intentionally does not provide
unverified snapshot SQL or automatic database recovery commands.