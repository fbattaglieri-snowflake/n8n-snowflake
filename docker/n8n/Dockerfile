ARG N8N_VERSION=2.38.6

FROM alpine:3.24 AS source
ARG N8N_VERSION
RUN apk add --no-cache ca-certificates git
RUN git clone --depth 1 --branch "n8n@${N8N_VERSION}" \
      https://github.com/n8n-io/n8n.git /src/n8n

FROM alpine:3.24 AS python
# The interpreter tree produced here is copied wholesale into the final image,
# so it is the tree that has to be clean: upgrading only the final image leaves
# the distro-managed copy of setuptools in place, with its metadata still
# recording the vulnerable version, and the image scan then reports a package
# that no pin in the final stage appears to govern.
RUN apk add --no-cache python3 python3-dev py3-pip && \
    python3 -m pip install --break-system-packages --no-cache-dir \
      --upgrade --force-reinstall "setuptools==84.0.0" "msgpack==1.2.1" && \
    find /usr/lib/python3.14 -maxdepth 3 -name 'setuptools-*.dist-info' \
      -not -name 'setuptools-84.0.0.dist-info' -exec rm -rf {} + && \
    find /usr/lib/python3.14 -maxdepth 3 -name 'msgpack-*.dist-info' \
      -not -name 'msgpack-1.2.1.dist-info' -exec rm -rf {} +

FROM alpine:3.24 AS package-tools
RUN apk add --no-cache apk-tools-static

FROM n8nio/n8n:${N8N_VERSION}

USER root

COPY --from=package-tools /sbin/apk.static /tmp/apk.static
RUN /tmp/apk.static upgrade --no-cache && \
    /tmp/apk.static add --no-cache 'libcrypto3>=3.5.8-r0' 'libssl3>=3.5.8-r0' 'libexpat>=2.8.5-r0' 'pcre2>=10.49-r0' && \
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
      --no-cache-dir "urllib3==2.8.0" "websockets>=15.0.1,<16" && \
    python3 -m pip install --break-system-packages --no-cache-dir \
      "msgpack==1.2.1" "setuptools==84.0.0" && \
    python3 -m pip check

# Assert the floors the image scan enforces, while the paths are still visible.
#
# The scan reports a package name and a version but frequently no path, so a
# stale second copy in one of the several interpreter trees in this image is
# expensive to locate from the report alone. Failing here instead names the
# directory.
COPY assert_python_floors.py /tmp/assert_python_floors.py
RUN python3 /tmp/assert_python_floors.py setuptools=78.1.1 msgpack=1.2.1 && \
    rm /tmp/assert_python_floors.py

USER node

