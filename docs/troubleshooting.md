# Troubleshooting

## HTTP Nodes Fail With `Please use OAuth when connecting to Snowflake`

Snowflake forbids programmatic access tokens from inside an SPCS container. The node is
calling the account endpoint directly with a PAT. Point it at the private proxy instead:
`http://<proxy-dns-name>:8080/api/v2/statements`. This is architectural, so there is no
header format or network policy that makes a PAT work from inside the cluster.

## Agent Fails With `Each 'toolUse' block must be accompanied with a matching 'toolResult' block`

An assistant turn carried more than one tool call. Cortex places each `tool` message in its
own turn, so the request arrives with one `toolResult` for N `toolUse` blocks. The proxy
collapses those turns; if you see this error, the deployed proxy image predates that fix.
Note that the rejected turn stays in the conversation history, so the session stays broken
until it is restarted, and that sending `parallel_tool_calls: false` does not help because
the error comes from the shape of the history rather than from generation.

## Agent Tool Fails With `has a 'supplyData' method but no 'execute' method`

The workflow uses a langchain tool node such as `@n8n/n8n-nodes-langchain.toolHttpRequest`.
Use the tool variant of the regular node instead: `n8n-nodes-base.httpRequestTool`,
`n8n-nodes-base.postgresTool`. Model-supplied arguments come from `$fromAI(...)`.

## Chat Model Node Fails Against the Proxy

Turn off **Use Responses API** on the node. The proxy implements `/v1/chat/completions` and
does not implement `/v1/responses`. Also confirm the model name is in the catalog served by
`GET /v1/models`: an unknown name returns `HTTP 400 unknown model`, which some clients
report as a context-length error.

## `ExpressionError: invalid syntax` Before the Node Runs

A nested object literal inside `{{ }}` produced two adjacent closing braces, which ends the
expression early. Write `} }` instead of `}}`.

## Expression Arrives at the Database as Literal Text

A field that mixes literal text with `{{ }}` needs a leading `=` on the parameter value.
Workflow validation reports this before a run.

## `Error in sub-node Simple Memory`

The memory node's default session key reads `$json.sessionId`, which only exists downstream
of a chat trigger. In a non-chat workflow set `sessionIdType` to a custom key, for example a
run identifier.

## Cortex Search Does Not Return a Document That Was Just Written

The service refreshes on `TARGET_LAG`, so a freshly inserted row is not indexed yet. Either
lower the lag and wait it out, or read back on a later run. If a different document outranks
yours, filter on an identifier of your own; only columns declared as `ATTRIBUTES` can be
filtered.

## Cortex Analyst Answers Only Part of the Question

Prose output is non-deterministic and a bundled prompt often comes back half answered. Ask
one thing at a time, or number the questions explicitly. Assert on the presence of a number
or a known label, never on an exact string.

## SQL API Returns `HTTP 422`

A value was concatenated into the statement and contained an apostrophe. Use parameter
bindings, which is also the only safe way to pass model-generated text.

## n8n Cannot Connect to Snowflake Postgres

- The symptom of a missing egress rule is a **connection timeout, not an authentication
  error**: check that `<instance-host>:5432` is in the network rule referenced by the
  external access integration attached to the n8n service.
- Verify the Postgres instance is ready before the compute pool and services start.
- Verify the instance has a network policy attached at all. Without one it accepts no
  connections, while still appearing healthy in `SHOW POSTGRES INSTANCES`.
- Verify the configured ingress CIDR reaches the Postgres endpoint.
- Verify the Snowflake Secret is granted to the service owner role.
- Check TLS settings and the Postgres hostname returned during bootstrap.

## The Postgres Application Password Was Lost

It is displayed once, by `CREATE POSTGRES INSTANCE`, and cannot be retrieved later. Do not
recreate the instance: `ALTER POSTGRES INSTANCE <name> RESET ACCESS FOR 'application';`
returns a new one. Update the Snowflake Secret and the n8n credential together.

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

