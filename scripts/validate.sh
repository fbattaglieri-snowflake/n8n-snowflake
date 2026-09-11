#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPOSITORY_ROOT"

python3 -m py_compile proxy/cortex/cortex_proxy.py proxy/ingress/n8n_ingress_proxy.py scripts/bootstrap_postgres.py scripts/export_workflows.py
python3 -m ruff check proxy scripts tests
python3 -m pytest proxy tests -q
node --check docker/n8n/patch-snowflake-spcs-oauth.js
bash -n scripts/wait_for_services.sh
python3 -m json.tool proxy/cortex/models.json >/dev/null
yamllint -d '{extends: default, rules: {line-length: disable, document-start: disable, truthy: disable, empty-lines: disable, braces: disable}}' \
  .github infrastructure/specs

if grep -RIE --exclude-dir=.git --exclude-dir=.venv \
  '(github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{20,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----)' .; then
  echo "Potential secret material detected" >&2
  exit 1
fi

echo "Validation passed"
