import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Redirects are not allowed for authenticated workflow exports")


def export_workflows(endpoint, ingress_token, api_key, output_path, opener=None):
    parsed = urllib.parse.urlsplit(endpoint)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not parsed.hostname.endswith(".snowflakecomputing.app")
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("N8N_BACKUP_ENDPOINT must be an HTTPS Snowflake ingress origin")
    if not ingress_token or not api_key:
        raise ValueError("Both ingress authentication and an n8n API key are required")
    if any(char in ingress_token + api_key for char in '\r\n"'):
        raise ValueError("Invalid authentication header value")
    if opener is None:
        opener = urllib.request.build_opener(NoRedirect())
    workflows = []
    seen_ids = set()
    seen_cursors = set()
    cursor = None
    for _ in range(10000):
        query = {"limit": 250}
        if cursor:
            query["cursor"] = cursor
        request = urllib.request.Request(
            endpoint.rstrip("/") + "/api/v1/workflows?" + urllib.parse.urlencode(query),
            headers={
                "Authorization": f'Snowflake Token="{ingress_token}"',
                "X-N8N-API-KEY": api_key,
                "Accept": "application/json",
            },
        )
        with opener.open(request, timeout=60) as response:
            page = json.load(response)
        if not isinstance(page, dict) or not isinstance(page.get("data"), list):
            raise ValueError("Invalid workflow export response")
        for workflow in page["data"]:
            if not isinstance(workflow, dict):
                raise ValueError("Invalid workflow record")
            workflow_id = workflow.get("id")
            if not isinstance(workflow_id, str) or not workflow_id or workflow_id in seen_ids:
                raise ValueError("Missing or duplicate workflow ID; export is incomplete")
            if not isinstance(workflow.get("nodes"), list):
                raise ValueError("Workflow export lacks node definitions")
            seen_ids.add(workflow_id)
            workflows.append(workflow)
        cursor = page.get("nextCursor")
        if cursor is None or cursor == "":
            break
        if not isinstance(cursor, str) or cursor in seen_cursors:
            raise ValueError("Invalid or repeated pagination cursor")
        seen_cursors.add(cursor)
    else:
        raise ValueError("Pagination limit reached; export is incomplete")
    if not workflows:
        raise ValueError("No workflows returned; refusing an empty backup")
    output_path = Path(output_path)
    with output_path.open("x", encoding="utf-8") as output:
        os.chmod(output_path, 0o600)
        json.dump(workflows, output, indent=2)
    return len(workflows)


if __name__ == "__main__":
    try:
        count = export_workflows(
            os.environ.get("N8N_BACKUP_ENDPOINT", ""),
            os.environ.get("N8N_BACKUP_INGRESS_TOKEN", ""),
            os.environ.get("N8N_BACKUP_API_KEY", ""),
            sys.argv[1],
        )
    except Exception as error:
        print(f"Workflow export failed ({type(error).__name__}); no upload", file=sys.stderr)
        sys.exit(1)
    print(f"Exported {count} workflows")