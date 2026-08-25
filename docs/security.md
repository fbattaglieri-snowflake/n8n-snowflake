# Security

## Threat Model

The deployment protects against accidental secret publication, untrusted pull-request code, credential reuse, unauthenticated n8n access, direct public exposure of the Cortex proxy, and accidental deletion of persistent state during upgrades.

It does not make arbitrary n8n community nodes trustworthy. Community nodes execute code in the n8n process and must be reviewed before installation.

## Credential Handling

- GitHub authenticates with OIDC workload identity federation.
- SPCS authenticates to Snowflake using `/snowflake/session/token`.
- The Postgres password and n8n encryption key are Snowflake Secret objects.
- The local management proxy accepts credentials only through environment variables or local key files.
- Proxy logs exclude authorization headers, API keys, request bodies, and response bodies.

## Pull Request Isolation

Pull request workflows use read-only GitHub permissions and never request an OIDC token. Deployment workflows use `workflow_dispatch`, protected environments, and explicit `id-token: write` permission.

## Least Privilege

The bootstrap role is used only to establish infrastructure. The production deployment role is intentionally narrower. Review grants after bootstrap and remove any privilege that is not required by the workflows enabled in your fork.

## Network Hardening

- Do not allow `0.0.0.0/0` into Snowflake Postgres.
- Prefer explicit n8n egress hostnames to wildcard internet access.
- Keep the Cortex proxy endpoint private.
- Keep Snowflake ingress authentication enabled for n8n.
- Use TLS verification for Postgres once the account-specific CA is available.

## Secret Scanning

CI runs Gitleaks and Trivy. GitHub secret scanning and push protection should also be enabled when available for the repository and account plan.

