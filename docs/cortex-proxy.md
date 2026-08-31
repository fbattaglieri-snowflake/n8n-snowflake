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

## Wire Differences the Proxy Absorbs

- `max_tokens` is rewritten to `max_completion_tokens`, which Cortex requires.
- A missing `finish_reason` is inferred, so clients that branch on `tool_calls` work.
- Models that reject `tools` unless `reasoning_effort` is `none` get it set for them,
  with an adaptive retry for models not yet in the catalog.
- **Streamed tool calls are renumbered.** On Claude-family models Cortex marks every
  parallel tool call with `index: 0`. A client reassembles fragments by index, so it merges
  the calls into one, executes a single tool and leaves an orphan `toolUse` in the history,
  which makes the next request fail. The proxy counts distinct call ids and rewrites the
  index. It is idempotent: on models that already number correctly nothing is rewritten.
- **Parallel tool calls are collapsed.** Cortex places each `tool` message in its own
  turn, so an assistant turn with N tool calls arrives with one `toolResult` for N
  `toolUse` blocks and is rejected with a non-retryable `HTTP 400 Each 'toolUse' block
  must be accompanied with a matching 'toolResult' block`. Because the rejected turn
  stays in the conversation history, the failure is permanent for that session rather
  than transient. The proxy keeps the first tool call and folds the other results into
  its content, so no tool output is lost. Sending `parallel_tool_calls: false` upstream
  does not help: the error comes from the shape of the history, not from generation.
  The visible trade-off is that tools run in successive turns instead of in parallel.

## Using the Proxy as an OpenAI-Compatible Endpoint in n8n

Any n8n node that speaks OpenAI can be pointed at the proxy, including the AI Agent
chat model. Create a credential of type **OpenAI** with:

- **Base URL**: `http://<proxy-dns-name>:8080/v1`, where the DNS name comes from
  `SHOW SERVICES LIKE 'CORTEX_PROXY_SERVICE'`, column `dns_name`.
- **API Key**: any placeholder string. The proxy authenticates to Snowflake with the
  service OAuth token and ignores this field, so no secret is stored in n8n.

Then on the chat model node:

- Pick the model from the list. The dropdown is populated from `GET /v1/models`, which
  serves the configured catalog.
- **Turn off "Use Responses API".** The proxy implements `/v1/chat/completions` only.

The result is that agents, chains and summarisation nodes run on Snowflake-served
models with no external provider in the path: prompts and data never leave Snowflake.

For a complete working example, see [`examples/memory-tour`](../examples/memory-tour).

## SQL Safety

Use SQL API parameter bindings for dynamic workflow values. Do not concatenate LLM output, user input, or workflow variables into SQL text.

