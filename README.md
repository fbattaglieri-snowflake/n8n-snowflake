# n8n on Snowflake

Deploy n8n Community Edition to Snowpark Container Services with Snowflake Postgres, durable block storage, Snowflake-native secrets, GitHub Actions OIDC, a native Snowflake node that uses the rotating SPCS service token, and an internal OpenAI-compatible proxy for Cortex AI and the Snowflake SQL API.

> **Disclaimer:** This independent project was developed and is maintained by **Francesco Battaglieri**, with the assistance of **Snowflake Cortex Code**. It is not an official Snowflake or n8n release, product, service, publication, integration, reference architecture, or support offering. **Neither Snowflake Inc. nor n8n GmbH, nor the n8n project maintainers, reviewed, approved, sponsored, endorsed, certified, authorized, commissioned, or warranted this project.** They are not responsible for its code, documentation, security, maintenance, support, deployment, operation, or results. Use is entirely at your own risk. See [DISCLAIMER.md](DISCLAIMER.md) for the full no-warranty, limitation-of-liability, non-affiliation, and user-responsibility terms.

## Architecture

```text
GitHub Actions                         Snowflake account
OIDC workload identity                dedicated deployment roles
        |                                      |
        +---- build linux/amd64 images --------+
                                               |
                                  Snowflake image repositories
                                               |
                         +---------------------+--------------------+
                         |                                          |
                 n8n SPCS service                         Cortex proxy service
                 public Snowflake ingress                 private SPCS endpoint
                 native Snowflake OAuth                   Cortex chat compatibility
                 50 GiB block volume                      SQL API forwarding
                         |
                  Snowflake Postgres
                  workflow and execution state
```

## Included Capabilities

- Reproducible n8n CE image pinned to an upstream release.
- Native n8n Snowflake node authentication through `/snowflake/session/token`.
- Snowflake Postgres as the n8n database.
- Persistent SPCS block storage for local n8n state and community nodes.
- Snowflake Secrets for the Postgres password and n8n encryption key.
- Internal proxy for `/api/v2/statements` and Cortex OpenAI compatibility.
- AI Agents whose LLM is served by Snowflake Cortex through that proxy, with no external model provider in the path.
- Documented patterns for reaching every Snowflake capability from a workflow: standard tables, Snowflake Postgres, Cortex Analyst, Cortex Search, Cortex Agents and model inference.
- Local proxy for managing the n8n REST API through Snowflake ingress.
- Secretless GitHub-to-Snowflake authentication with workload identity federation.
- Maintainer-approved bootstrap and deployment environments.
- CI, tests, container scanning, SBOM generation, and secret scanning.

## Prerequisites

- A Snowflake account with Snowpark Container Services and Snowflake Postgres available.
- A role allowed to perform the one-time OIDC trust setup.
- Docker or another OCI-compatible builder that can produce `linux/amd64` images.
- A public GitHub repository with Actions enabled.
- A Postgres ingress CIDR that reaches the Snowflake Postgres endpoint from the selected SPCS compute pool. Do not use `0.0.0.0/0` in production.

## Deployment Flow

1. Fork or clone the repository.
2. Review [docs/security.md](docs/security.md) and [docs/configuration.md](docs/configuration.md).
3. Run the one-time trust setup in `infrastructure/sql/00_oidc_trust.sql` as an account administrator.
4. Create the `bootstrap` and `production` GitHub environments and restrict their reviewers to the repository maintainer.
5. Configure repository variables described in [docs/configuration.md](docs/configuration.md). No Snowflake credential is required.
6. Run the **Bootstrap Snowflake** workflow manually.
7. Run the **Deploy to Snowflake** workflow manually and approve the `production` environment.
8. Verify the generated endpoint and complete n8n owner setup in the browser.

## Design Decisions

- **No long-lived Snowflake credential in GitHub.** GitHub OIDC tokens are short-lived and scoped to protected environments.
- **No Postgres password in workflow output.** Initial credentials are captured and converted into Snowflake Secret objects within a single Snowflake session.
- **No account-specific defaults.** Names, regions, endpoints, and roles are supplied as variables.
- **No public Cortex proxy.** n8n reaches it through private SPCS DNS.
- **No destructive upgrade.** Deployments use `ALTER SERVICE`; they do not drop the n8n service or its block volume.
- **Immutable deployment tags.** Images use the Git commit SHA rather than `latest`.

## Documentation

- [Architecture](docs/architecture.md)
- [Building workflows against every Snowflake capability](docs/building-workflows.md) — model inference, agents, Cortex Analyst, Cortex Search, standard tables and Snowflake Postgres, with the pitfalls of each
- [Configuration](docs/configuration.md)
- [Security](docs/security.md)
- [Operations](docs/operations.md)
- [Cortex and SQL proxy](docs/cortex-proxy.md)
- [n8n REST and MCP access](docs/n8n-management.md)
- [Troubleshooting](docs/troubleshooting.md)

## Examples

- [Snowflake Memory Tour](examples/memory-tour) — one workflow that writes to and reads back from a standard table (via Cortex Analyst), a document corpus (via Cortex Search) and Snowflake Postgres, then has an AI Agent reason across all three with a Cortex-served model.

## License

Repository-authored code and documentation are licensed under Apache-2.0. n8n and all other upstream dependencies retain their own licenses. Review [DISCLAIMER.md](DISCLAIMER.md) and [NOTICE](NOTICE) before using or redistributing this project.
