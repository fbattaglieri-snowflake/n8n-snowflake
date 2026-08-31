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


def parallel_turn():
    return {
        "model": "model-a",
        "tools": [{"type": "function"}],
        "messages": [
            {"role": "user", "content": "call both"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"id": "a", "function": {"name": "alpha", "arguments": "{}"}},
                    {"id": "b", "function": {"name": "beta", "arguments": "{}"}},
                ],
            },
            {"role": "tool", "tool_call_id": "a", "content": "alpha=11"},
            {"role": "tool", "tool_call_id": "b", "content": "beta=22"},
        ],
    }


def test_collapses_parallel_tool_calls_and_keeps_every_result():
    output = MODULE.rewrite_chat_request(parallel_turn(), config())
    assistant = output["messages"][1]
    assert len(assistant["tool_calls"]) == 1
    assert assistant["tool_calls"][0]["id"] == "a"
    tool_messages = [m for m in output["messages"] if m["role"] == "tool"]
    assert len(tool_messages) == 1
    assert tool_messages[0]["tool_call_id"] == "a"
    assert "alpha=11" in tool_messages[0]["content"]
    assert "beta=22" in tool_messages[0]["content"]
    assert "[beta]" in tool_messages[0]["content"]


def test_collapse_does_not_mutate_the_caller_document():
    original = parallel_turn()
    MODULE.rewrite_chat_request(original, config())
    assert len(original["messages"][1]["tool_calls"]) == 2


def test_single_tool_call_is_untouched():
    body = parallel_turn()
    body["messages"][1]["tool_calls"] = [body["messages"][1]["tool_calls"][0]]
    body["messages"] = body["messages"][:3]
    output = MODULE.rewrite_chat_request(body, config())
    assert len(output["messages"]) == 3
    assert output["messages"][2]["content"] == "alpha=11"


def test_orphan_results_are_reattached_to_the_kept_call():
    body = parallel_turn()
    body["messages"] = [body["messages"][0], body["messages"][1], body["messages"][3]]
    output = MODULE.rewrite_chat_request(body, config())
    tool_messages = [m for m in output["messages"] if m["role"] == "tool"]
    assert len(tool_messages) == 1
    assert tool_messages[0]["tool_call_id"] == "a"
    assert "beta=22" in tool_messages[0]["content"]


def test_flattens_block_style_tool_content():
    body = parallel_turn()
    body["messages"][3]["content"] = [{"type": "text", "text": "beta=22"}]
    output = MODULE.rewrite_chat_request(body, config())
    tool_messages = [m for m in output["messages"] if m["role"] == "tool"]
    assert "beta=22" in tool_messages[0]["content"]
