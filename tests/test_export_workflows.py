import importlib.util
import io
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "export_workflows", Path(__file__).parents[1] / "scripts/export_workflows.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
ENDPOINT = "https://example.snowflakecomputing.app"


class FakeOpener:
    def __init__(self, pages):
        self.pages = iter(pages)
        self.requests = []

    def open(self, request, timeout):
        assert timeout == 60
        self.requests.append(request)
        page = next(self.pages)
        if isinstance(page, Exception):
            raise page
        return io.StringIO(json.dumps(page))


def test_export_paginates_and_supplies_both_auth_headers(tmp_path):
    opener = FakeOpener([
        {"data": [{"id": "one", "nodes": []}], "nextCursor": "next+page"},
        {"data": [{"id": "two", "nodes": []}]},
    ])
    destination = tmp_path / "export.json"
    assert MODULE.export_workflows(ENDPOINT, "test-token", "test-key", destination, opener) == 2
    assert len(json.loads(destination.read_text())) == 2
    assert "cursor=next%2Bpage" in opener.requests[1].full_url
    headers = {key.lower(): value for key, value in opener.requests[0].header_items()}
    assert headers["authorization"] == 'Snowflake Token="test-token"'
    assert headers["x-n8n-api-key"] == "test-key"
    assert destination.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("pages", [
    [{"data": []}],
    [{"error": "denied"}],
    [{"data": [{"id": "one"}]}],
    [{"data": [{"id": "one", "nodes": []}], "nextCursor": "x"}, OSError("offline")],
    [{"data": [{"id": "one", "nodes": []}], "nextCursor": "x"},
     {"data": [{"id": "one", "nodes": []}]}],
    [{"data": [], "nextCursor": "x"}, {"data": [], "nextCursor": "x"}],
])
def test_incomplete_export_never_produces_file(tmp_path, pages):
    destination = tmp_path / "export.json"
    with pytest.raises((ValueError, OSError)):
        MODULE.export_workflows(ENDPOINT, "test-token", "test-key", destination, FakeOpener(pages))
    assert not destination.exists()


@pytest.mark.parametrize("endpoint", ["http://example.snowflakecomputing.app",
                                       "https://example.org", ENDPOINT + "/path",
                                       ENDPOINT + "?query=x"])
def test_rejects_invalid_origin_before_authentication(tmp_path, endpoint):
    opener = FakeOpener([])
    with pytest.raises(ValueError):
        MODULE.export_workflows(endpoint, "test-token", "test-key", tmp_path / "out", opener)
    assert not opener.requests


def test_rejects_redirect():
    with pytest.raises(ValueError, match="Redirects"):
        MODULE.NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.org")


def test_requires_both_credentials(tmp_path):
    with pytest.raises(ValueError, match="Both"):
        MODULE.export_workflows(ENDPOINT, "", "", tmp_path / "out", FakeOpener([]))