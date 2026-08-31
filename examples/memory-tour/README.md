# Example: Snowflake Memory Tour

One n8n workflow that writes to and reads back from every Snowflake memory reachable
from an SPCS-hosted n8n, then lets an AI Agent reason across all of them with an LLM
served by Snowflake Cortex.

Nothing in this example calls an external model provider. The prompts, the data and
the answers stay inside Snowflake.

For the patterns behind it, generalised and explained one capability at a time, read
[`docs/building-workflows.md`](../../docs/building-workflows.md).

## What it demonstrates

| Memory | Write | Read |
|---|---|---|
| Standard table | `INSERT` and `UPDATE` over the Snowflake SQL API | Cortex Analyst, in natural language |
| Document corpus | `INSERT` of a new chunk | Cortex Search |
| Snowflake Postgres | `INSERT` and `UPDATE` with the native Postgres node | plain `SELECT`, no Cortex layer |
| All three at once | — | AI Agent with three tools, LLM on the Cortex proxy |

## Why every call goes through the proxy

Snowflake forbids programmatic access tokens from inside an SPCS container: a bearer
PAT is rejected with *"Please use OAuth when connecting to Snowflake from inside a
container"*. The Cortex proxy in [`proxy/cortex`](../../proxy/cortex) reads the
service OAuth token from `/snowflake/session/token` on every request, so it is the
only authenticated path out of the cluster. It exposes:

| Path | Used by |
|---|---|
| `POST /api/v2/statements` | every SQL statement, including Analyst and Search |
| `POST /v1/chat/completions` | the AI Agent chat model |
| `GET /v1/models` | the model dropdown in the n8n credential |

A consequence worth knowing before you design your own workflow: the **Cortex Analyst
REST API is not reachable through the proxy**, which only whitelists the two paths
above. Analyst is therefore called as SQL, through an agent and
`SNOWFLAKE.CORTEX.DATA_AGENT_RUN`. Cortex Search has a SQL entry point of its own,
`SNOWFLAKE.CORTEX.SEARCH_PREVIEW`.

## Prerequisites

1. n8n and the Cortex proxy deployed as described in [`docs/architecture.md`](../../docs/architecture.md).
2. A Snowflake Postgres instance reachable from the compute pool, with its host on
   port 5432 present in the egress network rule attached to the n8n service.
3. Two n8n credentials:
   - `Snowflake LLMs`, type **OpenAI**, base URL `http://<proxy-dns-name>:8080/v1`.
     The API key field is a placeholder, the proxy authenticates with OAuth. See
     [`docs/cortex-proxy.md`](../../docs/cortex-proxy.md).
   - `Memory Demo Postgres`, type **Postgres**, SSL on, certificate verification off.

## Install

```bash
snow sql -f sql/10_objects.sql
snow sql -f sql/20_seed.sql
snow sql -f sql/30_cortex.sql
cortex agent-studio agent-deploy --file-path sql/40_agent.yaml \
  --fqn MEMORY_DEMO.CORE.MEMORY_DEMO_AGENT
```

Then import `workflow.json` into n8n and replace the placeholders:

| Placeholder | Where to find the real value |
|---|---|
| `CORTEX_PROXY_DNS_NAME` | `SHOW SERVICES LIKE 'CORTEX_PROXY_SERVICE'`, column `dns_name` |
| `REPLACE_WITH_YOUR_OPENAI_CREDENTIAL_ID` | the id of your `Snowflake LLMs` credential |
| `REPLACE_WITH_YOUR_POSTGRES_CREDENTIAL_ID` | the id of your Postgres credential |

The Postgres table is created by the workflow itself with `CREATE TABLE IF NOT
EXISTS`, so there is no manual step on that side.

## Running it

Click **Execute workflow**, or `POST` to the `memory-tour` webhook. A run takes about
100 seconds, most of it the deliberate wait described below. The final Code node
prints a report saying, for each memory, what was written and what came back.

## Things that will bite you

**Cortex Search has a target lag.** The service in this example is created with
`TARGET_LAG = '1 minute'` and the workflow waits 70 seconds before searching, because
it reads back a chunk it has just written. Without the wait the chunk is simply not
indexed yet. The search is also filtered on the current run id, so a hit is proof of
the round trip rather than a lucky match on a pre-existing document.

**Parameter binding is mandatory.** Concatenating values into the statement fails with
`HTTP 422` as soon as a value contains an apostrophe, and it is the only safe way to
pass model-generated text.

**Two adjacent closing braces end an n8n expression.** A nested object literal inside
`{{ }}` that produces `}}` makes n8n report `invalid syntax` before the node runs.
Space them out as `} }`.

**Use the tool variants of regular nodes.** `n8n-nodes-base.httpRequestTool` and
`n8n-nodes-base.postgresTool`, not `@n8n/n8n-nodes-langchain.toolHttpRequest`: on
current n8n the latter fails with *"has a 'supplyData' method but no 'execute'
method"*. Arguments come from the model through `$fromAI(...)`.

**Turn the Responses API off** on the chat model node. The proxy implements
`/v1/chat/completions`; it does not implement `/v1/responses`.

**Simple Memory needs an explicit session key.** Its default reads `$json.sessionId`,
which only exists downstream of a chat trigger. This example keys it on the run id.

**The webhook responds before the report exists.** With a Wait node in the path, n8n
answers the HTTP request when the execution suspends. Poll the execution, or move the
wait out of the request path, if you need the report in the response body.

## Cost

The Postgres instance is the only always-on component: `BURST_S` with 10 GB, the
smallest configuration available. `ALTER POSTGRES INSTANCE ... SUSPEND` stops the
compute charge; storage and the ten days of backups keep accruing. The warehouse is
`XSMALL` with a 60 second auto-suspend, and the first Analyst call of the day pays a
warehouse cold start of 20 to 30 seconds.
