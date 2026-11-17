ARG N8N_VERSION=2.34.5

FROM alpine:3.24 AS source
ARG N8N_VERSION
RUN apk add --no-cache ca-certificates git
RUN git clone --depth 1 --branch "n8n@${N8N_VERSION}" \
      https://github.com/n8n-io/n8n.git /src/n8n

FROM alpine:3.24 AS python
RUN apk add --no-cache python3 python3-dev py3-pip && \
    mkdir -p /usr/local/lib/node_modules/@n8n/task-runner-python && \
    python3 -m venv --without-pip /usr/local/lib/node_modules/@n8n/task-runner-python/.venv && \
    python3 -m pip --python /usr/local/lib/node_modules/@n8n/task-runner-python/.venv/bin/python install \
      --no-cache-dir --upgrade pip "urllib3>=2.8.0" "websockets>=15.0.1,<16"

FROM n8nio/n8n:${N8N_VERSION}

USER root

COPY --from=python /usr/bin/python3 /usr/bin/python3
COPY --from=python /usr/lib/python3.14 /usr/lib/python3.14
COPY --from=python /usr/lib/libpython3.14.so.1.0 /usr/lib/libpython3.14.so.1.0
COPY --from=python /usr/lib/libpython3.so /usr/lib/libpython3.so
COPY --from=source /src/n8n/packages/@n8n/task-runner-python \
  /usr/local/lib/node_modules/@n8n/task-runner-python
COPY --from=python /usr/local/lib/node_modules/@n8n/task-runner-python/.venv \
  /usr/local/lib/node_modules/@n8n/task-runner-python/.venv
COPY patch-snowflake-spcs-oauth.js /tmp/patch-snowflake-spcs-oauth.js

RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/lib/libpython3.14.so.1.0 /usr/lib/libpython3.14.so && \
    node /tmp/patch-snowflake-spcs-oauth.js && \
    rm /tmp/patch-snowflake-spcs-oauth.js && \
    /usr/local/lib/node_modules/@n8n/task-runner-python/.venv/bin/python -c "import urllib3, websockets"

USER node
