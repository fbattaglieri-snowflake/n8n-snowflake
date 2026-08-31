-- MEMORY_DEMO: field-service domain backing the n8n "Snowflake Memory Tour" demo.
-- Standard tables (written and updated by n8n, read back through Cortex Analyst),
-- a document corpus (written by n8n, read back through Cortex Search).
-- Snowflake Postgres lives outside this script: it is a separate instance.

CREATE DATABASE IF NOT EXISTS MEMORY_DEMO
  COMMENT = 'Demo domain: n8n writing to and reading from every Snowflake memory';

CREATE SCHEMA IF NOT EXISTS MEMORY_DEMO.CORE
  COMMENT = 'Tables, document corpus, search service and semantic view for the demo';

CREATE WAREHOUSE IF NOT EXISTS MEMORY_DEMO_WH
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Serves Cortex Search refresh and Cortex Analyst for the memory demo';

-- Standard table. n8n inserts and updates rows here through the SQL API.
CREATE TABLE IF NOT EXISTS MEMORY_DEMO.CORE.SERVICE_TICKETS (
    TICKET_ID       STRING DEFAULT UUID_STRING(),
    RUN_ID          STRING,
    SITE            STRING,
    ASSET           STRING,
    SEVERITY        STRING,
    STATUS          STRING,
    SENTIMENT_SCORE FLOAT,
    NOTE            STRING,
    SOURCE          STRING,
    CREATED_AT      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT      TIMESTAMP_NTZ
)
COMMENT = 'Field service tickets. SOURCE says which system wrote the row.';

-- Document corpus behind the Cortex Search service.
CREATE TABLE IF NOT EXISTS MEMORY_DEMO.CORE.SERVICE_DOCS (
    DOC_ID     STRING DEFAULT UUID_STRING(),
    RUN_ID     STRING,
    TITLE      STRING,
    CHUNK      STRING,
    SOURCE     STRING,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Maintenance procedure chunks. n8n appends new chunks at run time.';

-- Failures reported by the workflow error branch.
CREATE TABLE IF NOT EXISTS MEMORY_DEMO.CORE.DEMO_RUN_LOG (
    RUN_ID    STRING,
    WORKFLOW  STRING,
    NODE      STRING,
    MESSAGE   STRING,
    LOGGED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Failures reported by the n8n memory tour error branch';
