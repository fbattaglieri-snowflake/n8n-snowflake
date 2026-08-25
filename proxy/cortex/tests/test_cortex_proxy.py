import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "cortex_proxy.py"
SPEC = importlib.util.spec_from_file_location("cortex_proxy", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def config():
    return MODULE.ModelConfig(
        models=("model-a",),
        tools_require_none=frozenset({"model-a"}),
        tools_unsupported=frozenset({"model-b"}),
    )


def test_rewrites_max_tokens_and_reasoning():
    output = MODULE.rewrite_chat_request(
        {"model": "model-a", "max_tokens": 42, "tools": [{"type": "function"}]},
        config(),
    )
    assert "max_tokens" not in output
    assert output["max_completion_tokens"] == 42
    assert output["reasoning_effort"] == "none"


def test_rejects_unsupported_tool_model():
    try:
        MODULE.rewrite_chat_request(
            {"model": "model-b", "tools": [{"type": "function"}]},
            config(),
        )
    except ValueError as error:
        assert "does not support tool calling" in str(error)
    else:
        raise AssertionError("expected ValueError")


def test_normalizes_non_stream_finish_reason():
    raw = json.dumps(
        {"choices": [{"finish_reason": "", "message": {"tool_calls": [{"id": "x"}]}}]}
    ).encode()
    output = json.loads(MODULE.normalize_chat_response(raw))
    assert output["choices"][0]["finish_reason"] == "tool_calls"


def test_injects_stream_terminal_reason():
    raw = b'data: {"id":"x","model":"m","choices":[{"delta":{"content":"ok"}}]}\n\ndata: [DONE]\n\n'
    output = MODULE.normalize_stream(raw)
    assert b'"finish_reason":"stop"' in output
    assert output.endswith(b"data: [DONE]\n\n")


def test_model_list():
    output = json.loads(MODULE.model_response(config()))
    assert output["data"][0]["id"] == "model-a"
