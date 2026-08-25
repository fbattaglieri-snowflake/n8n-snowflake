#!/usr/bin/env python3
"""Local proxy that authenticates to Snowflake ingress and the n8n REST API."""

from __future__ import annotations

import base64
import datetime
import hashlib
import http.server
import os
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

UPSTREAM = os.environ.get("N8N_UPSTREAM", "").rstrip("/")
LISTEN_HOST = os.environ.get("N8N_PROXY_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("N8N_PROXY_PORT", "8099"))
N8N_API_KEY = os.environ.get("N8N_API_KEY", "")
KEY_PATH = Path(os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH", "")).expanduser()
ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT", "")
USER = os.environ.get("SNOWFLAKE_USER", "")
PAT = os.environ.get("SNOWFLAKE_PAT", "")
JWT_TTL_MINUTES = 55
JWT_RENEW_BEFORE = datetime.timedelta(minutes=5)

SKIP_REQUEST_HEADERS = {
    "host",
    "authorization",
    "x-n8n-api-key",
    "connection",
    "keep-alive",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "content-length",
    "accept-encoding",
}
SKIP_RESPONSE_HEADERS = {
    "connection",
    "keep-alive",
    "transfer-encoding",
    "content-encoding",
    "content-length",
}


class SnowflakeIngressAuth:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._token: str | None = None
        self._expires: datetime.datetime | None = None
        self._private_key: Any = None
        if not PAT:
            self._private_key = self._load_private_key()

    @staticmethod
    def _load_private_key() -> Any:
        if not KEY_PATH or not KEY_PATH.exists():
            raise RuntimeError("configure SNOWFLAKE_PAT or a valid SNOWFLAKE_PRIVATE_KEY_PATH")
        if not ACCOUNT or not USER:
            raise RuntimeError(
                "SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER are required for key-pair auth"
            )
        from cryptography.hazmat.primitives import serialization

        return serialization.load_pem_private_key(KEY_PATH.read_bytes(), password=None)

    def _fingerprint(self) -> str:
        from cryptography.hazmat.primitives import serialization

        public_der = self._private_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        digest = hashlib.sha256(public_der).digest()
        return "SHA256:" + base64.b64encode(digest).decode("ascii")

    def _mint_jwt(self) -> tuple[str, datetime.datetime]:
        import jwt

        now = datetime.datetime.now(datetime.timezone.utc)
        expires = now + datetime.timedelta(minutes=JWT_TTL_MINUTES)
        account = ACCOUNT.upper()
        user = USER.upper()
        token = jwt.encode(
            {
                "iss": f"{account}.{user}.{self._fingerprint()}",
                "sub": f"{account}.{user}",
                "iat": now,
                "exp": expires,
            },
            self._private_key,
            algorithm="RS256",
        )
        return token, expires

    def header(self) -> str:
        if PAT:
            return f'Snowflake Token="{PAT}"'
        with self._lock:
            now = datetime.datetime.now(datetime.timezone.utc)
            if (
                self._token is None
                or self._expires is None
                or now >= self._expires - JWT_RENEW_BEFORE
            ):
                self._token, self._expires = self._mint_jwt()
        return f'Snowflake Token="{self._token}"'


AUTH: SnowflakeIngressAuth | None = None


def forward_headers(source: Any, authorization: str, n8n_api_key: str) -> dict[str, str]:
    headers = {
        key: value for key, value in source.items() if key.lower() not in SKIP_REQUEST_HEADERS
    }
    headers["Authorization"] = authorization
    headers["X-N8N-API-KEY"] = n8n_api_key
    return headers


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "n8n-snowflake-ingress-proxy/1.0"

    def log_message(self, format_string: str, *args: Any) -> None:
        return

    def proxy(self) -> None:
        if AUTH is None:
            raise RuntimeError("authentication is not initialized")
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else None
        request = urllib.request.Request(  # noqa: S310 - validated HTTPS upstream
            UPSTREAM + self.path,
            data=body,
            headers=forward_headers(self.headers, AUTH.header(), N8N_API_KEY),
            method=self.command,
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
                payload, status, output_headers = response.read(), response.status, response.headers
        except urllib.error.HTTPError as error:
            payload, status, output_headers = error.read(), error.code, error.headers
        except Exception:
            payload, status, output_headers = b'{"error":"upstream request failed"}', 502, {}

        self.send_response(status)
        for key, value in output_headers.items():
            if key.lower() not in SKIP_RESPONSE_HEADERS:
                self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = do_POST = do_PATCH = do_PUT = do_DELETE = do_HEAD = proxy


def main() -> None:
    global AUTH
    if not UPSTREAM.startswith("https://"):
        raise RuntimeError("N8N_UPSTREAM must be an HTTPS URL")
    if not N8N_API_KEY:
        raise RuntimeError("N8N_API_KEY is required")
    AUTH = SnowflakeIngressAuth()
    AUTH.header()
    print(f"n8n ingress proxy listening on {LISTEN_HOST}:{LISTEN_PORT}", flush=True)
    http.server.ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
