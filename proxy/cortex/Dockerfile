FROM python:3.12-slim

RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY cortex_proxy.py /opt/cortex_proxy.py
COPY models.json /opt/models.json

ENV CORTEX_PROXY_BIND=0.0.0.0 \
    CORTEX_PROXY_PORT=8080 \
    CORTEX_MODELS_PATH=/opt/models.json \
    PYTHONUNBUFFERED=1

USER 65534:65534
EXPOSE 8080
ENTRYPOINT ["python3", "-u", "/opt/cortex_proxy.py"]
