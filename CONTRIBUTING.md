# Contributing

Contributions are welcome through issues and pull requests.

## Development Rules

1. Do not commit credentials, private keys, tokens, real account identifiers, or private endpoint URLs.
2. Keep deployment examples parameterized and use placeholder values.
3. Pin dependencies and GitHub Actions to explicit versions or immutable commits.
4. Add tests for changes to authentication, request forwarding, SQL generation, or service specifications.
5. Run `./scripts/validate.sh` before opening a pull request.
6. Keep all repository content in English.

All changes require review and approval from `@fbattaglieri-snowflake`. The maintainer may close suggestions that increase credential exposure, weaken least privilege, or make the deployment account-specific.

