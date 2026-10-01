# Safe n8n upgrades on SPCS

## Candidate status: 2026-10-01

The candidate is n8n **2.41.5**. It is not deployment-approved. Image build,
version reporting, native Snowflake OAuth patch checks, Python SSL/SQLite imports,
and local repository validation passed. The full image scan remains blocking:
38 HIGH JavaScript findings across 10 upstream dependency packages, plus four
Python findings that require reconciling embedded upstream SBOM data with the
installed filesystem. These are scanner findings, not counts of unique CVEs.
There are no HIGH/CRITICAL OS findings after explicitly refreshing OpenSSL and
Expat; no dependency trees or unfixed findings are excluded from the image scan.

Affected JavaScript packages include axios, nodemailer, toml, undici,
@grpc/grpc-js, @tiptap/core, @xmldom/xmldom, adm-zip, brace-expansion, and fast-uri.
Some available fixes require major dependency changes. Do not overwrite pnpm
package directories, remove SBOMs, or suppress findings to obtain a green gate.
Use a compatible upstream release or a separately reviewed and tested source
rebuild. Successful image creation does not establish migration safety.

## Before changing a live service

1. Capture the live service specification, image digest, endpoints, external
   access integrations, mounted volumes and secret references in private storage.
   Never use a repository example specification to overwrite a running service.
2. Inventory all application data, not just workflows: published versions,
   credentials, users, projects, permissions, variables, installed packages,
   execution history, pending executions and files. Test credential decryption
   without persisting or printing plaintext. Preserve the encryption key.
3. Build and scan a version-pinned candidate, preserving the SPCS OAuth patch and
   matching Python runner. Verify the actual runtime, not just build success.
4. Test migration against an independent database fork and a volume restored from
   a snapshot. Block workflow execution, timers, waiting-execution recovery and
   outbound application actions before the cloned server can start. Never start
   two Telegram pollers or other competing event consumers.
5. Verify rollback using the old image with an unmigrated database copy and the
   corresponding volume. A fork changed by a migration rehearsal is not a
   pre-upgrade recovery point.

## Maintenance and final backup

- Coordinate a maintenance window. Ensure external producers buffer/retry events;
  schedules may not replay missed intervals. An unchanged database alone cannot
  guarantee no events are lost during downtime.
- Prevent new starts and edits, drain running work, and preserve waiting runs.
- After stopping writes and flushing files, create a fresh independent database
  fork and volume snapshot. Verify readiness, readability and fingerprints.
- A snapshot taken while production is running is useful for rehearsal, but is
  not proof of a coherent database-plus-files recovery point.
- Only after every gate passes, use `ALTER SERVICE` with the verified immutable
  image/digest. Preserve the existing endpoint, volume, secrets and configuration.
  Never drop the live service for an upgrade.
- Compare application integrity before reopening intake. Then observe normal
  scheduled executions; do not run business workflows merely as smoke tests.

## Rollback boundaries

Before intake resumes, a failed migration needs a coordinated rollback of image,
database and files. Returning only to the old image against a migrated database
is not a safe rollback.

After new writes have been accepted, preserve both database states and reconcile
them before rollback. Restoring the old backup at that point can discard new
data. Retain verified backup resources until the operator approves cleanup;
suspended compute still incurs storage charges.

The repository deployment workflow is **not** an implementation of this runbook:
it also deploys the Cortex proxy and repository specification. Do not dispatch it
as a shortcut for an n8n-only upgrade of an existing customized deployment.