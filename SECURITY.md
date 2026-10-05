# Security Policy

## Reporting a Vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub private vulnerability reporting when available, or contact the maintainer through the private contact method listed on the GitHub profile.

Include the affected component, reproduction steps, impact, and any proposed mitigation. Do not include live credentials, access tokens, account identifiers, private endpoint URLs, or customer data.

This process is provided on a best-effort basis and does not create a warranty, support obligation, or service-level commitment. See [DISCLAIMER.md](DISCLAIMER.md).

## Security Model

- GitHub Actions authenticates to Snowflake with short-lived OIDC workload identity tokens.
- Snowflake credentials, Postgres passwords, and the n8n encryption key are never stored in GitHub.
- Runtime secrets are Snowflake Secret objects injected into SPCS containers.
- The Cortex proxy is private to SPCS service networking.
- The n8n public endpoint remains behind Snowflake ingress authentication.
- Pull request workflows never receive deployment permissions or secrets.
- Deployment requires manual approval by the repository maintainer.
- Every pull request builds both container images and scans them. The gate blocks on vulnerabilities this repository can fix and reports the rest without blocking, so that a red build always means there is an action to take. See [docs/security.md](docs/security.md#container-image-vulnerability-gate).

See [docs/security.md](docs/security.md) for the threat model and hardening guidance.
