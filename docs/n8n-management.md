# n8n REST and MCP Management

Snowflake ingress and n8n use different authentication headers:

- Snowflake ingress consumes `Authorization: Snowflake Token="..."`.
- The n8n REST API reads `X-N8N-API-KEY`.

The local ingress proxy adds both headers and forwards requests to the Snowflake ingress URL. It is intended for local administrative tooling such as `n8n-mcp`.

## Local Setup

1. Store the n8n REST API key in a local secret manager.
2. Use a Snowflake key pair or PAT for the ingress credential.
3. Start `proxy/ingress/n8n_ingress_proxy.py` with credentials injected as environment variables.
4. Configure `n8n-mcp` with `N8N_API_URL=http://127.0.0.1:8099` and a non-empty placeholder `N8N_API_KEY`.
5. Set `WEBHOOK_SECURITY_MODE=moderate`. Strict mode blocks loopback management traffic in affected `n8n-mcp` releases.

Do not put real secret values in MCP JSON configuration files. Some clients pass those values literally rather than resolving secret references.

