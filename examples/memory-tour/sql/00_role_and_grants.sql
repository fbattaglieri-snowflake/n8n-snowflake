-- =============================================================================
-- 00_role_and_grants.sql
-- Least-privilege Snowflake role setup for the "Snowflake Memory Tour" example.
--
-- External readers do NOT need the maintainer's Snowflake account or ACCOUNTADMIN
-- at workflow runtime. Run this script once as USERADMIN / ACCOUNTADMIN, and
-- replace <YOUR_SPCS_SERVICE_OWNER_ROLE> with the role that owns CORTEX_PROXY_SERVICE
-- (and N8N_SERVICE / LLM_PROXY_STANDARD / LLM_PROXY_AIGATEWAY) in your account.
-- =============================================================================

USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS MEMORY_DEMO_ROLE
  COMMENT = 'Least-privilege runtime role for the n8n Snowflake Memory Tour example';

-- Allow the role hierarchy and your SPCS service owner role to assume MEMORY_DEMO_ROLE
GRANT ROLE MEMORY_DEMO_ROLE TO ROLE SYSADMIN;
-- Uncomment and set your SPCS service owner role (for example N8N_SERVICE_ROLE):
-- GRANT ROLE MEMORY_DEMO_ROLE TO ROLE <YOUR_SPCS_SERVICE_OWNER_ROLE>;

-- Cortex SQL / REST API and Cortex AI Gateway access
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE MEMORY_DEMO_ROLE;
GRANT USAGE ON AI GATEWAY SNOWFLAKE TO ROLE MEMORY_DEMO_ROLE;
