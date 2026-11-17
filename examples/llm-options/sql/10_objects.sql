-- =============================================================================
-- 10_objects.sql
-- Synthetic database, auto-suspend XS warehouse, fleet table, and Semantic View
-- backing the native Snowflake node and Cortex Agent branches in LLM_Options.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS LLM_OPTIONS_DEMO
  COMMENT = 'Synthetic demo domain for the n8n LLM_Options multi-API showcase';

CREATE SCHEMA IF NOT EXISTS LLM_OPTIONS_DEMO.CORE
  COMMENT = 'Synthetic industrial fleet opportunities and semantic view';

CREATE WAREHOUSE IF NOT EXISTS LLM_OPTIONS_DEMO_WH
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'XS auto-suspend warehouse for the n8n LLM_Options showcase';

CREATE TABLE IF NOT EXISTS LLM_OPTIONS_DEMO.CORE.FLEET_OPPORTUNITIES (
    OPPORTUNITY_ID       STRING DEFAULT UUID_STRING(),
    RANK                 NUMBER(10, 0),
    ASSET_MODEL          STRING,
    REGION               STRING,
    POTENTIAL_SCORE      FLOAT,
    REVENUE_POTENTIAL    FLOAT,
    NEXT_BEST_ACTION     STRING,
    OPERATING_HOURS      FLOAT,
    MAINTENANCE_PRIORITY STRING,
    RECOMMENDED_ACTION   STRING,
    URGENCY_DAYS         NUMBER(10, 0),
    CREATED_AT           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Synthetic industrial equipment maintenance opportunities queried by n8n';

CREATE OR REPLACE SEMANTIC VIEW LLM_OPTIONS_DEMO.CORE.FLEET_ANALYTICS
  TABLES (
    fleet AS LLM_OPTIONS_DEMO.CORE.FLEET_OPPORTUNITIES
      PRIMARY KEY (OPPORTUNITY_ID)
      WITH SYNONYMS ('fleet', 'opportunities', 'assets', 'equipment')
      COMMENT = 'One row per synthetic industrial fleet maintenance opportunity'
  )
  FACTS (
    fleet.potential_score AS POTENTIAL_SCORE
      COMMENT = 'Opportunity score from 0 to 100',
    fleet.revenue_potential AS REVENUE_POTENTIAL
      COMMENT = 'Estimated service revenue in EUR',
    fleet.operating_hours AS OPERATING_HOURS
      COMMENT = 'Cumulative equipment operating hours',
    fleet.urgency_days AS URGENCY_DAYS
      COMMENT = 'Recommended action window in days'
  )
  DIMENSIONS (
    fleet.opportunity_id AS OPPORTUNITY_ID
      COMMENT = 'Unique opportunity identifier',
    fleet.asset_model AS ASSET_MODEL
      WITH SYNONYMS ('model', 'machine', 'equipment model')
      COMMENT = 'Synthetic equipment model code',
    fleet.region AS REGION
      WITH SYNONYMS ('territory', 'area', 'plant region')
      COMMENT = 'Operating region',
    fleet.next_best_action AS NEXT_BEST_ACTION
      WITH SYNONYMS ('action', 'recommendation type')
      COMMENT = 'Recommended commercial action',
    fleet.maintenance_priority AS MAINTENANCE_PRIORITY
      WITH SYNONYMS ('priority', 'criticality')
      COMMENT = 'Priority tier: high, medium, or low'
  )
  METRICS (
    fleet.opportunity_count AS COUNT(fleet.opportunity_id)
      WITH SYNONYMS ('count', 'number of opportunities'),
    fleet.total_revenue_potential AS SUM(fleet.revenue_potential)
      WITH SYNONYMS ('total revenue', 'pipeline value'),
    fleet.avg_potential_score AS AVG(fleet.potential_score)
      WITH SYNONYMS ('average score')
  )
  COMMENT = 'Semantic view over synthetic industrial fleet opportunities for LLM_Options';

-- Least-privilege runtime grants for N8N_DEMO_ROLE
GRANT USAGE ON WAREHOUSE LLM_OPTIONS_DEMO_WH TO ROLE N8N_DEMO_ROLE;
GRANT USAGE ON DATABASE LLM_OPTIONS_DEMO TO ROLE N8N_DEMO_ROLE;
GRANT USAGE ON SCHEMA LLM_OPTIONS_DEMO.CORE TO ROLE N8N_DEMO_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA LLM_OPTIONS_DEMO.CORE TO ROLE N8N_DEMO_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA LLM_OPTIONS_DEMO.CORE TO ROLE N8N_DEMO_ROLE;
GRANT SELECT, REFERENCES ON SEMANTIC VIEW LLM_OPTIONS_DEMO.CORE.FLEET_ANALYTICS TO ROLE N8N_DEMO_ROLE;
