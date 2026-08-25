# Troubleshooting

## n8n Cannot Connect to Snowflake Postgres

- Verify the Postgres instance is ready before the compute pool and services start.
- Verify the configured ingress CIDR reaches the Postgres endpoint.
- Verify the Snowflake Secret is granted to the service owner role.
- Check TLS settings and the Postgres hostname returned during bootstrap.

## Native Snowflake Node Requests a Password

Confirm the custom image was deployed and the SPCS token file exists. The patch intentionally preserves the upstream credential behavior outside SPCS.

## Cortex AI Node Returns `max_tokens is deprecated`

Confirm the workflow points to the private Cortex proxy rather than the upstream Cortex endpoint directly.

## Repeated or Truncated AI Responses

Check that the proxy emits a terminal `finish_reason`. Some upstream responses leave it blank, which causes clients to retry or treat the response as truncated.

## n8n MCP Management Tools Cannot Reach Loopback

Set `WEBHOOK_SECURITY_MODE=moderate` for the MCP process. Do not use permissive mode unless you have reviewed the additional SSRF exposure.

## Local Proxy Returns Invalid JSON

Ensure the proxy removes `Accept-Encoding` before forwarding. Otherwise n8n can return Brotli-compressed data that a simple proxy forwards without the corresponding encoding header.

