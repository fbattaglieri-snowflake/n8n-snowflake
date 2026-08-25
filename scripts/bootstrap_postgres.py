#!/usr/bin/env python3
"""Create Snowflake Postgres and store its application password as a Snowflake Secret."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from typing import Any


def run_snow(arguments: list[str], *, capture: bool = False, input_text: str | None = None) -> str:
    command = ["snow", *arguments]
    result = subprocess.run(  # noqa: S603 - fixed executable with argument list
        command,
        check=True,
        capture_output=capture,
        text=True,
        input=input_text,
        env=os.environ.copy(),
    )
    return result.stdout if capture else ""


def quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def configure_network(args: argparse.Namespace) -> str:
    rule = f"{args.database}.{args.schema}.N8N_POSTGRES_INGRESS"
    policy = "N8N_POSTGRES_NETWORK_POLICY"
    statements = [
        (
            f"CREATE NETWORK RULE IF NOT EXISTS {rule} "
            "TYPE = IPV4 MODE = POSTGRES_INGRESS "
            f"VALUE_LIST = ({quote(args.ingress_cidr)}) "
            f"COMMENT = {quote('Restrictive ingress for n8n Snowflake Postgres')}"
        ),
        (
            f"CREATE NETWORK POLICY IF NOT EXISTS {policy} "
            f"ALLOWED_NETWORK_RULE_LIST = ({quote(rule)}) "
            f"COMMENT = {quote('Network policy for n8n Snowflake Postgres')}"
        ),
    ]
    for statement in statements:
        run_snow(["sql", "--temporary-connection", "--silent", "--query", statement])
    return policy


def create_instance(args: argparse.Namespace, network_policy: str) -> dict[str, Any]:
    sql = (
        f"CREATE POSTGRES INSTANCE {args.instance} "
        f"COMPUTE_FAMILY = {quote(args.compute_family)} "
        f"STORAGE_SIZE_GB = {args.storage_gb} "
        "AUTHENTICATION_AUTHORITY = POSTGRES "
        f"POSTGRES_VERSION = {args.postgres_version} "
        f"NETWORK_POLICY = {quote(network_policy)} "
        f"COMMENT = {quote('n8n Community Edition database')}"
    )
    output = run_snow(
        [
            "sql",
            "--temporary-connection",
            "--format",
            "JSON_EXT",
            "--silent",
            "--query",
            sql,
        ],
        capture=True,
    )
    rows = json.loads(output)
    if not rows:
        raise RuntimeError("Snowflake Postgres creation returned no result")
    return rows[0]


def save_secret_and_egress(args: argparse.Namespace, creation: dict[str, Any]) -> None:
    access_roles = creation.get("access_roles") or creation.get("ACCESS_ROLES")
    host = creation.get("host") or creation.get("HOST")
    if isinstance(access_roles, str):
        access_roles = json.loads(access_roles)
    application = (access_roles or {}).get("application")
    if not application or not host:
        raise RuntimeError("Snowflake Postgres creation result is missing required fields")
    password = application.get("password") if isinstance(application, dict) else None
    if not password:
        raise RuntimeError("application password is missing from creation result")

    secret_sql = (
        f"CREATE SECRET IF NOT EXISTS {args.database}.{args.schema}.N8N_PG_PASSWORD "
        "TYPE = GENERIC_STRING "
        f"SECRET_STRING = {quote(password)} "
        f"COMMENT = {quote('Snowflake Postgres application password for n8n')};"
    )
    run_snow(
        ["sql", "--temporary-connection", "--silent", "--stdin"],
        input_text=secret_sql,
    )
    grant_sql = (
        f"GRANT READ ON SECRET {args.database}.{args.schema}.N8N_PG_PASSWORD "
        f"TO ROLE {args.deploy_role}"
    )
    run_snow(["sql", "--temporary-connection", "--silent", "--query", grant_sql])
    postgres_grant_sql = (
        f"GRANT USAGE, MONITOR ON POSTGRES INSTANCE {args.instance} TO ROLE {args.deploy_role}"
    )
    run_snow(["sql", "--temporary-connection", "--silent", "--query", postgres_grant_sql])

    postgres_rule = f"{args.database}.{args.schema}.N8N_POSTGRES_EGRESS"
    web_rule = f"{args.database}.{args.schema}.N8N_EGRESS_WEB"
    egress_sql = (
        f"CREATE NETWORK RULE IF NOT EXISTS {postgres_rule} "
        "TYPE = HOST_PORT MODE = EGRESS "
        f"VALUE_LIST = ({quote(str(host) + ':5432')}) "
        f"COMMENT = {quote('n8n access to Snowflake Postgres')}"
    )
    run_snow(["sql", "--temporary-connection", "--silent", "--query", egress_sql])
    integration_sql = (
        f"ALTER EXTERNAL ACCESS INTEGRATION {args.egress_integration} "
        f"SET ALLOWED_NETWORK_RULES = ({web_rule}, {postgres_rule})"
    )
    run_snow(["sql", "--temporary-connection", "--silent", "--query", integration_sql])
    print("Snowflake Postgres credentials were stored as Snowflake Secrets.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--compute-family", required=True)
    parser.add_argument("--storage-gb", type=int, required=True)
    parser.add_argument("--postgres-version", type=int, default=17)
    parser.add_argument("--ingress-cidr", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--deploy-role", required=True)
    parser.add_argument("--egress-integration", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.storage_gb < 10:
        raise ValueError("Snowflake Postgres storage must be at least 10 GiB")
    try:
        network_policy = configure_network(args)
        creation = create_instance(args, network_policy)
        save_secret_and_egress(args, creation)
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from error


if __name__ == "__main__":
    main()
