import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "n8n_ingress_proxy.py"
SPEC = importlib.util.spec_from_file_location("n8n_ingress_proxy", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class Headers:
    def items(self):
        return [
            ("Accept-Encoding", "br"),
            ("Authorization", "client-value"),
            ("X-N8N-API-KEY", "client-key"),
            ("Content-Type", "application/json"),
        ]


def test_forward_headers_replaces_credentials_and_encoding():
    output = MODULE.forward_headers(Headers(), 'Snowflake Token="jwt"', "api-key")
    assert output["Authorization"] == 'Snowflake Token="jwt"'
    assert output["X-N8N-API-KEY"] == "api-key"
    assert "Accept-Encoding" not in output
    assert output["Content-Type"] == "application/json"
