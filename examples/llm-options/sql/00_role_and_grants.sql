-- =============================================================================
-- 00_role_and_grants.sql
-- Least-privilege Snowflake role setup for the "LLM_Options" showcase example.
--
-- External readers do NOT have (and do NOT need) the maintainer's Snowflake
-- account. Run this script once on your own Snowflake account, and grant
-- N8N_DEMO_ROLE to your SPCS service owner role so both the native Snowflake
-- node and CORTEX_PROXY_SERVICE can execute queries without ACCOUNTADMIN.
-- =============================================================================

USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS N8N_DEMO_ROLE
  COMMENT = 'Least-privilege runtime role for the n8n LLM_Options showcase workflow';

-- Grant into SYSADMIN hierarchy and to your SPCS service owner role:
GRANT ROLE N8N_DEMO_ROLE TO ROLE SYSADMIN;
-- Uncomment and replace <YOUR_SPCS_SERVICE_OWNER_ROLE> (e.g., N8N_SERVICE_ROLE):
-- GRANT ROLE N8N_DEMO_ROLE TO ROLE <YOUR_SPCS_SERVICE_OWNER_ROLE>;

-- Grant Cortex SQL / Cortex REST API and Cortex AI Gateway usage
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE N8N_DEMO_ROLE;
GRANT USAGE ON AI GATEWAY SNOWFLAKE TO ROLE N8N_DEMO_ROLE;
