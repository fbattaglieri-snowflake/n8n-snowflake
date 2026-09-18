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

## Container Image Vulnerability Gate

Every pull request builds both images and scans them twice.

The **blocking** scan fails the build on CRITICAL and HIGH vulnerabilities, restricted to what this repository can fix. Two categories are excluded:

- **Unfixed vulnerabilities** (`ignore-unfixed`). A CVE with no released fix cannot be cleared by any change here. Blocking on it would make every build red regardless of the diff, which trains reviewers to ignore the gate.
- **The upstream n8n dependency tree** (`usr/local/lib/node_modules/n8n/node_modules`). These packages arrive inside the `n8nio/n8n` base image and are replaced only by a new upstream release. The lever is the `N8N_VERSION` pin, not a package override: forcing a newer version inside that tree would ship a combination upstream never tested.

The **advisory** scan covers the whole image, including both excluded categories, and never fails the build. Its purpose is that the excluded debt stays visible on every run rather than disappearing from view. Both scans are rendered by `scripts/summarize_trivy.py`, which prints CVE identifiers, installed and fixed versions, and the package path to the job summary.

Consequences to keep in mind:

- A red build means there is an action to take. Treat it as such.
- A growing advisory list is the signal to bump `N8N_VERSION`. Review it when deciding whether an upstream upgrade is due.
- Packages installed by this repository are governed at build time by `docker/n8n/assert_python_floors.py`, which fails the build if any copy of a distribution is below its security floor and names the directory holding it. Adding a pin without raising the floor leaves the gap the assertion exists to catch.

