-- Creates reusable Snowflake objects. The Snowflake Postgres instance is created
-- separately with scripts/bootstrap_postgres.py so generated credentials never
-- pass through GitHub logs.

USE ROLE <% bootstrap_role %>;

CREATE DATABASE IF NOT EXISTS <% database %>
  COMMENT = 'n8n Community Edition on Snowflake';
CREATE SCHEMA IF NOT EXISTS <% database %>.<% schema %>;

CREATE WAREHOUSE IF NOT EXISTS <% warehouse %>
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Deployment warehouse for n8n on Snowflake';

CREATE COMPUTE POOL IF NOT EXISTS <% compute_pool %>
  MIN_NODES = 1
  MAX_NODES = 1
  INSTANCE_FAMILY = <% instance_family %>
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  AUTO_SUSPEND_SECS = 3600
  COMMENT = 'SPCS compute pool for n8n and its private proxy';

CREATE IMAGE REPOSITORY IF NOT EXISTS
  <% database %>.<% schema %>.<% n8n_image_repository %>;
CREATE IMAGE REPOSITORY IF NOT EXISTS
  <% database %>.<% schema %>.<% proxy_image_repository %>;
CREATE STAGE IF NOT EXISTS <% database %>.<% schema %>.N8N_CONFIG
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

CREATE NETWORK RULE IF NOT EXISTS <% database %>.<% schema %>.N8N_EGRESS_WEB
  TYPE = HOST_PORT
  MODE = EGRESS
  VALUE_LIST = ('0.0.0.0:443', '0.0.0.0:80')
  COMMENT = 'Default n8n web egress. Replace with explicit workflow destinations.';

CREATE EXTERNAL ACCESS INTEGRATION IF NOT EXISTS <% egress_integration %>
  ALLOWED_NETWORK_RULES = (<% database %>.<% schema %>.N8N_EGRESS_WEB)
  ALLOWED_AUTHENTICATION_SECRETS = NONE
  ENABLED = TRUE
  COMMENT = 'Outbound web access for n8n workflows';

EXECUTE IMMEDIATE $$
DECLARE
  encryption_key VARCHAR DEFAULT UUID_STRING() || UUID_STRING();
  statement_text VARCHAR DEFAULT
    'CREATE SECRET IF NOT EXISTS <% database %>.<% schema %>.N8N_ENCRYPTION_KEY '
    || 'TYPE = GENERIC_STRING SECRET_STRING = ? '
    || 'COMMENT = ''n8n credential encryption key generated inside Snowflake''';
BEGIN
  EXECUTE IMMEDIATE :statement_text USING (encryption_key);
  RETURN 'n8n encryption key is stored in Snowflake';
END;
$$;

GRANT USAGE ON DATABASE <% database %> TO ROLE <% deploy_role %>;
GRANT USAGE ON SCHEMA <% database %>.<% schema %> TO ROLE <% deploy_role %>;
GRANT USAGE ON WAREHOUSE <% warehouse %> TO ROLE <% deploy_role %>;
GRANT USAGE, MONITOR, OPERATE ON COMPUTE POOL <% compute_pool %> TO ROLE <% deploy_role %>;
GRANT READ, WRITE ON IMAGE REPOSITORY
  <% database %>.<% schema %>.<% n8n_image_repository %> TO ROLE <% deploy_role %>;
GRANT READ, WRITE ON IMAGE REPOSITORY
  <% database %>.<% schema %>.<% proxy_image_repository %> TO ROLE <% deploy_role %>;
GRANT READ, WRITE ON STAGE <% database %>.<% schema %>.N8N_CONFIG TO ROLE <% deploy_role %>;
GRANT CREATE SERVICE ON SCHEMA <% database %>.<% schema %> TO ROLE <% deploy_role %>;
GRANT USAGE ON INTEGRATION <% egress_integration %> TO ROLE <% deploy_role %>;
GRANT READ ON SECRET <% database %>.<% schema %>.N8N_ENCRYPTION_KEY TO ROLE <% deploy_role %>;
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE <% deploy_role %>;
