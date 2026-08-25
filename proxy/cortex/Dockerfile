FROM python:3.12-slim

RUN useradd --create-home --uid 10001 proxy
COPY cortex_proxy.py /opt/cortex_proxy.py
COPY models.json /opt/models.json

ENV CORTEX_PROXY_BIND=0.0.0.0 \
    CORTEX_PROXY_PORT=8080 \
    CORTEX_MODELS_PATH=/opt/models.json \
    PYTHONUNBUFFERED=1

USER proxy
EXPOSE 8080
ENTRYPOINT ["python3", "-u", "/opt/cortex_proxy.py"]

