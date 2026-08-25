# Cortex and SQL Proxy

## Why It Exists

n8n AI nodes speak an OpenAI-compatible protocol, while Cortex behavior differs in a few client-sensitive areas. The proxy provides a stable compatibility layer and also allows n8n workflows to call the Snowflake SQL API without storing credentials.

## Routes

- `POST /v1/chat/completions`: forwards to Cortex chat completions.
- `GET /v1/models`: returns the configured model catalog.
- `POST /api/v2/statements`: forwards to the Snowflake SQL API.
- `GET /healthz`: process health.

## Authentication

The proxy reads `/snowflake/session/token` for every upstream request and sends it as OAuth together with `SNOWFLAKE_HOST`. The token is refreshed by Snowflake and is usable only within the service.

## SQL Safety

Use SQL API parameter bindings for dynamic workflow values. Do not concatenate LLM output, user input, or workflow variables into SQL text.

