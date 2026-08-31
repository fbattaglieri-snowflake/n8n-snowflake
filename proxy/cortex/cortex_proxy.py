#!/usr/bin/env python3
"""Private SPCS proxy for Cortex chat completions and the Snowflake SQL API."""

from __future__ import annotations

import copy
import http.client
import http.server
import json
import os
import re
import socketserver
import ssl
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TOKEN_PATH = Path(os.environ.get("SNOWFLAKE_TOKEN_PATH", "/snowflake/session/token"))
UPSTREAM_HOST = os.environ.get("SNOWFLAKE_HOST", "")
BIND_HOST = os.environ.get("CORTEX_PROXY_BIND", "0.0.0.0")  # noqa: S104 - container listener
BIND_PORT = int(os.environ.get("CORTEX_PROXY_PORT", "8080"))
MODELS_PATH = Path(os.environ.get("CORTEX_MODELS_PATH", "/opt/models.json"))
MAX_REQUEST_BYTES = int(os.environ.get("CORTEX_PROXY_MAX_REQUEST_BYTES", str(10 * 1024 * 1024)))
CHAT_PATH = "/api/v2/cortex/v1/chat/completions"
SQL_PATH = "/api/v2/statements"
REASONING_TOOLS_ERROR = "function tools with reasoning_effort"

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


@dataclass(frozen=True)
class ModelConfig:
    models: tuple[str, ...]
    tools_require_none: frozenset[str]
    tools_unsupported: frozenset[str]


def load_model_config(path: Path = MODELS_PATH) -> ModelConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    models = tuple(str(value) for value in data.get("models", []))
    if not models:
        raise ValueError("models.json must contain at least one model")
    return ModelConfig(
        models=models,
        tools_require_none=frozenset(data.get("tools_require_reasoning_effort_none", [])),
        tools_unsupported=frozenset(data.get("tools_unsupported", [])),
    )


def read_service_token(path: Path = TOKEN_PATH) -> str:
    token = path.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError("SPCS OAuth token file is empty")
    return token


def tool_content_text(content: Any) -> str:
    """Flatten OpenAI tool-result content, which may be a string or a list of blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    if content is None:
        return ""
    return json.dumps(content, separators=(",", ":"))


def collapse_parallel_tool_calls(body: dict[str, Any]) -> dict[str, Any]:
    """Reduce every assistant turn to a single tool call, merging the other results as text.

    Cortex places each ``tool`` message in its own conversation turn, so a turn carrying N
    tool calls arrives upstream with one ``toolResult`` for N ``toolUse`` blocks and is
    rejected with a non-retryable HTTP 400. Agent frameworks emit parallel tool calls
    routinely, and the rejected turn stays in the conversation history, so the failure is
    permanent for that session. Keeping the first call and folding the remaining results
    into its content preserves the 1:1 pairing without discarding information.
    """
    messages = body.get("messages")
    if not isinstance(messages, list):
        return body

    keep_for: dict[str, str] = {}
    names: dict[str, str] = {}
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        calls = message.get("tool_calls")
        if not isinstance(calls, list) or len(calls) < 2:
            continue
        for call in calls:
            function = call.get("function") if isinstance(call, dict) else None
            name = (function or {}).get("name") if isinstance(function, dict) else None
            names[str((call or {}).get("id"))] = str(name or "tool")
        primary = str(calls[0].get("id"))
        for call in calls[1:]:
            keep_for[str(call.get("id"))] = primary
        message["tool_calls"] = [calls[0]]

    if not keep_for:
        return body

    merged: dict[str, list[str]] = {}
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "tool":
            continue
        call_id = str(message.get("tool_call_id"))
        if call_id in keep_for:
            label = names.get(call_id, "tool")
            text = tool_content_text(message.get("content"))
            merged.setdefault(keep_for[call_id], []).append(f"[{label}] {text}")

    kept: list[Any] = []
    seen_primary: set[str] = set()
    for message in messages:
        if isinstance(message, dict) and message.get("role") == "tool":
            call_id = str(message.get("tool_call_id"))
            if call_id in keep_for:
                continue
            extras = merged.get(call_id)
            if extras:
                seen_primary.add(call_id)
                own = tool_content_text(message.get("content"))
                message["content"] = "\n\n".join([own, *extras]) if own else "\n\n".join(extras)
        kept.append(message)

    for primary, extras in merged.items():
        if primary not in seen_primary:
            kept.append(
                {"role": "tool", "tool_call_id": primary, "content": "\n\n".join(extras)}
            )

    body["messages"] = kept
    return body


def rewrite_chat_request(body: dict[str, Any], config: ModelConfig) -> dict[str, Any]:
    rewritten = collapse_parallel_tool_calls(copy.deepcopy(body))
    if "max_tokens" in rewritten and "max_completion_tokens" not in rewritten:
        rewritten["max_completion_tokens"] = rewritten.pop("max_tokens")

    model = str(rewritten.get("model", ""))
    if rewritten.get("tools") and model in config.tools_unsupported:
        raise ValueError(f"model {model!r} does not support tool calling")
    if rewritten.get("tools") and model in config.tools_require_none:
        rewritten["reasoning_effort"] = "none"
    return rewritten


def infer_finish_reason(choice: dict[str, Any]) -> str:
    message = choice.get("message") or {}
    if message.get("tool_calls"):
        return "tool_calls"
    return "stop"


def normalize_chat_response(payload: bytes) -> bytes:
    document = json.loads(payload)
    for choice in document.get("choices", []):
        if not choice.get("finish_reason"):
            choice["finish_reason"] = infer_finish_reason(choice)
    return json.dumps(document, separators=(",", ":")).encode("utf-8")


def model_response(config: ModelConfig) -> bytes:
    data = [
        {"id": model, "object": "model", "created": 0, "owned_by": "snowflake"}
        for model in config.models
    ]
    return json.dumps({"object": "list", "data": data}, separators=(",", ":")).encode()


def terminal_stream_chunk(last_data: dict[str, Any] | None) -> bytes:
    chunk_id = (last_data or {}).get("id", "chatcmpl-proxy")
    model = (last_data or {}).get("model", "")
    chunk = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": 0,
        "model": model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    return f"data: {json.dumps(chunk, separators=(',', ':'))}\n\n".encode()


def reindex_tool_calls(document: dict[str, Any], state: dict[str, Any]) -> bool:
    """Renumber streamed tool-call fragments so each call keeps its own index.

    On Claude-family models Cortex marks every parallel tool call with ``index: 0``.
    A client reassembles fragments by index, so it merges the calls into one,
    executes a single tool and returns one ``toolResult`` for two ``toolUse``
    blocks; the next request is then rejected with
    ``HTTP 400 Each 'toolUse' block must be accompanied with a matching
    'toolResult' block``.

    A fragment carrying a non-empty ``id`` opens a new call, later fragments only
    carry a slice of ``arguments``. Counting distinct ids and using the counter as
    the index restores the pairing. Comparing against the last id makes this
    idempotent: on models that already number correctly the recomputed indexes
    match the originals and nothing is rewritten.
    """
    changed = False
    for choice in document.get("choices") or []:
        if not isinstance(choice, dict):
            continue
        for fragment in (choice.get("delta") or {}).get("tool_calls") or []:
            if not isinstance(fragment, dict):
                continue
            call_id = fragment.get("id") or ""
            if call_id and call_id != state.get("last_id"):
                state["count"] = state.get("count", 0) + 1
                state["last_id"] = call_id
            index = max(state.get("count", 1) - 1, 0)
            if fragment.get("index") != index:
                fragment["index"] = index
                changed = True
    return changed


def normalize_stream(payload: bytes) -> bytes:
    output: list[bytes] = []
    last_data: dict[str, Any] | None = None
    has_terminal_reason = False
    tool_state: dict[str, Any] = {}

    for raw_line in payload.splitlines(keepends=True):
        stripped = raw_line.strip()
        if stripped == b"data: [DONE]":
            if not has_terminal_reason:
                output.append(terminal_stream_chunk(last_data))
            output.append(b"data: [DONE]\n\n")
            continue
        if stripped.startswith(b"data: "):
            try:
                last_data = json.loads(stripped[6:])
                choices = last_data.get("choices", [])
                has_terminal_reason = has_terminal_reason or any(
                    choice.get("finish_reason") for choice in choices
                )
                if reindex_tool_calls(last_data, tool_state):
                    payload_line = json.dumps(last_data, separators=(",", ":"))
                    raw_line = f"data: {payload_line}\n\n".encode()
            except (json.JSONDecodeError, AttributeError):
                pass
        output.append(raw_line)
    return b"".join(output).rstrip(b"\n") + b"\n\n"


def sanitized_error(error: Exception) -> str:
    message = re.sub(r"(?i)(authorization|token|password|secret)[^\s,;]*", "credential", str(error))
    return message[:300]


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "n8n-snowflake-cortex-proxy/1.0"

    def log_message(self, format_string: str, *args: Any) -> None:
        sys.stderr.write(f"{self.command} {urllib.parse.urlsplit(self.path).path} {args[1]}\n")

    def send_payload(self, status: int, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_REQUEST_BYTES:
            raise ValueError("request body exceeds configured limit")
        return self.rfile.read(length)

    def upstream_headers(self) -> dict[str, str]:
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in HOP_BY_HOP
            and key.lower() not in {"host", "authorization", "content-length", "accept-encoding"}
        }
        headers["Authorization"] = f"Bearer {read_service_token()}"
        headers["X-Snowflake-Authorization-Token-Type"] = "OAUTH"
        return headers

    def upstream_request(self, path: str, body: bytes) -> tuple[int, dict[str, str], bytes]:
        if not UPSTREAM_HOST:
            raise RuntimeError("SNOWFLAKE_HOST is not configured")
        connection = http.client.HTTPSConnection(
            UPSTREAM_HOST,
            timeout=180,
            context=ssl.create_default_context(),
        )
        connection.request("POST", path, body=body, headers=self.upstream_headers())
        response = connection.getresponse()
        payload = response.read()
        headers = {key.lower(): value for key, value in response.getheaders()}
        connection.close()
        return response.status, headers, payload

    def do_GET(self) -> None:
        path = urllib.parse.urlsplit(self.path).path.rstrip("/")
        if path in {"", "/healthz"}:
            self.send_payload(200, b'{"status":"ok"}', "application/json")
            return
        if path in {"/v1/models", "/models"}:
            self.send_payload(200, model_response(load_model_config()), "application/json")
            return
        self.send_payload(404, b'{"error":"not found"}', "application/json")

    def do_POST(self) -> None:
        path = urllib.parse.urlsplit(self.path).path
        try:
            raw_body = self.read_body()
            if path in {"/v1/chat/completions", CHAT_PATH}:
                request_document = json.loads(raw_body)
                rewritten = rewrite_chat_request(request_document, load_model_config())
                status, headers, payload = self.upstream_request(
                    CHAT_PATH,
                    json.dumps(rewritten, separators=(",", ":")).encode(),
                )
                if (
                    status == 400
                    and rewritten.get("tools")
                    and REASONING_TOOLS_ERROR in payload.decode("utf-8", errors="ignore").lower()
                ):
                    rewritten["reasoning_effort"] = "none"
                    status, headers, payload = self.upstream_request(
                        CHAT_PATH,
                        json.dumps(rewritten, separators=(",", ":")).encode(),
                    )
                content_type = headers.get("content-type", "application/json")
                if status < 300 and request_document.get("stream"):
                    payload = normalize_stream(payload)
                    content_type = "text/event-stream"
                elif status < 300:
                    payload = normalize_chat_response(payload)
                self.send_payload(status, payload, content_type)
                return
            if path == SQL_PATH:
                status, headers, payload = self.upstream_request(SQL_PATH, raw_body)
                self.send_payload(status, payload, headers.get("content-type", "application/json"))
                return
            self.send_payload(404, b'{"error":"not found"}', "application/json")
        except (ValueError, json.JSONDecodeError) as error:
            payload = json.dumps({"error": sanitized_error(error)}).encode()
            self.send_payload(400, payload, "application/json")
        except Exception as error:  # noqa: BLE001
            payload = json.dumps({"error": sanitized_error(error)}).encode()
            self.send_payload(502, payload, "application/json")


def main() -> None:
    load_model_config()
    server = ThreadingHTTPServer((BIND_HOST, BIND_PORT), Handler)
    print(f"cortex proxy listening on {BIND_HOST}:{BIND_PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
