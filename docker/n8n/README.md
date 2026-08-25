# n8n Image

The image is based on an explicit n8n release tag and adds two capabilities:

1. The upstream Python task runner at the same release tag.
2. An SPCS-specific authentication path for the native Snowflake node.

When `/snowflake/session/token` exists, new Snowflake node connections use the rotating service OAuth token and the `SNOWFLAKE_HOST` and `SNOWFLAKE_ACCOUNT` environment variables supplied by SPCS. Outside SPCS, the upstream password and key-pair behavior is unchanged.

Build with:

```bash
docker build --platform linux/amd64 \
  --build-arg N8N_VERSION=2.34.5 \
  -t n8n-snowflake:2.34.5 \
  docker/n8n
```

The patch uses stable anchors in the compiled n8n node. A build fails rather than silently producing an unpatched image if an upstream release changes those anchors.

