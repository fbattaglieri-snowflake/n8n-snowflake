# n8n Image

The image is based on an explicit n8n release tag and adds two capabilities:

1. The upstream Python task runner at the same release tag.
2. An SPCS-specific authentication path for the native Snowflake node.

When `/snowflake/session/token` exists, new Snowflake node connections use the rotating service OAuth token and the `SNOWFLAKE_HOST` and `SNOWFLAKE_ACCOUNT` environment variables supplied by SPCS. Outside SPCS, the upstream password and key-pair behavior is unchanged.

Build with:

```bash
docker build --platform linux/amd64 \
  --build-arg N8N_VERSION=2.41.5 \
  -t n8n-snowflake:2.41.5 \
  docker/n8n
```

The patch uses stable anchors in the compiled n8n node. A build fails rather than silently producing an unpatched image if an upstream release changes those anchors.

The current candidate is **not deployment-approved**: the complete image security
scan is blocking. See [Safe upgrades](../../docs/safe-upgrade.md) for status,
backup, rehearsal, maintenance and rollback requirements.

Run the credential-free smoke check against the built image:

```bash
docker run --rm --network none \
  -v "$PWD/docker/n8n/smoke-test.js:/tmp/smoke-test.js:ro" \
  --entrypoint node n8n-snowflake:2.41.5 /tmp/smoke-test.js 2.41.5
```

