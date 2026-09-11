ARG N8N_VERSION=2.38.6

FROM alpine:3.24 AS source
ARG N8N_VERSION
RUN apk add --no-cache ca-certificates git
RUN git clone --depth 1 --branch "n8n@${N8N_VERSION}" \
      https://github.com/n8n-io/n8n.git /src/n8n

FROM alpine:3.24 AS python
RUN apk add --no-cache python3 python3-dev py3-pip

FROM alpine:3.24 AS package-tools
RUN apk add --no-cache apk-tools-static

FROM n8nio/n8n:${N8N_VERSION}

USER root

COPY --from=package-tools /sbin/apk.static /tmp/apk.static
RUN /tmp/apk.static upgrade --no-cache && \
    /tmp/apk.static add --no-cache 'libcrypto3>=3.5.8-r0' 'libssl3>=3.5.8-r0' 'libexpat>=2.8.4-r0' && \
    rm /tmp/apk.static

COPY --from=python /usr/bin/python3 /usr/bin/python3
COPY --from=python /usr/lib/python3.14 /usr/lib/python3.14
COPY --from=python /usr/lib/libpython3.14.so.1.0 /usr/lib/libpython3.14.so.1.0
COPY --from=python /usr/lib/libpython3.so /usr/lib/libpython3.so
COPY --from=python /usr/lib/libsqlite3.so.0 /usr/lib/libsqlite3.so.0
COPY --from=source /src/n8n/packages/@n8n/task-runner-python \
  /usr/local/lib/node_modules/@n8n/task-runner-python
COPY patch-snowflake-spcs-oauth.js /tmp/patch-snowflake-spcs-oauth.js

RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/lib/libpython3.14.so.1.0 /usr/lib/libpython3.14.so && \
    node /tmp/patch-snowflake-spcs-oauth.js && \
    rm /tmp/patch-snowflake-spcs-oauth.js && \
    python3 -m venv /usr/local/lib/node_modules/@n8n/task-runner-python/.venv && \
    /usr/local/lib/node_modules/@n8n/task-runner-python/.venv/bin/pip install \
      --no-cache-dir --upgrade pip && \
    /usr/local/lib/node_modules/@n8n/task-runner-python/.venv/bin/pip install \
      --no-cache-dir "urllib3==2.7.0" "websockets>=15.0.1,<16" && \
    python3 -m pip install --break-system-packages --no-cache-dir \
      "msgpack==1.2.1" "setuptools==78.1.1" && \
    python3 -m pip check

USER node

