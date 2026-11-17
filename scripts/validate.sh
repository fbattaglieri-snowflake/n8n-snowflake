#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPOSITORY_ROOT"

PYTHON_BIN="${PYTHON_BIN:-$(command -v python || command -v python3)}"

"$PYTHON_BIN" -m py_compile proxy/cortex/cortex_proxy.py proxy/ingress/n8n_ingress_proxy.py scripts/bootstrap_postgres.py
ruff check proxy scripts
pytest proxy -q
node --check docker/n8n/patch-snowflake-spcs-oauth.js
"$PYTHON_BIN" -m json.tool proxy/cortex/models.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/memory-tour/workflow.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/llm-options/workflow.json >/dev/null
yamllint -d '{extends: default, rules: {line-length: disable, document-start: disable, truthy: disable, empty-lines: disable, braces: disable}}' \
  .github infrastructure/specs examples/memory-tour/sql/40_agent.yaml examples/llm-options/sql/40_agent.yaml

if grep -RIE --exclude-dir=.git --exclude-dir=.venv \
  '(github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{20,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----)' .; then
  echo "Potential secret material detected" >&2
  exit 1
fi

echo "Validation passed"
