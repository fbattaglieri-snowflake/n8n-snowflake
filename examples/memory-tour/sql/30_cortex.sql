-- Cortex Search over the document corpus, and the semantic view that Cortex
-- Analyst uses to answer natural-language questions about the standard table.
--
-- TARGET_LAG is deliberately one minute: the demo writes a document chunk and
-- reads it back through Cortex Search inside the same n8n execution, so the
-- indexing lag has to be shorter than the workflow.

CREATE OR REPLACE CORTEX SEARCH SERVICE MEMORY_DEMO.CORE.DOC_SEARCH
  ON CHUNK
  ATTRIBUTES DOC_ID, RUN_ID, TITLE, SOURCE
  WAREHOUSE = MEMORY_DEMO_WH
  TARGET_LAG = '1 minute'
  COMMENT = 'Searchable maintenance corpus for the n8n memory demo'
  AS
    SELECT DOC_ID, RUN_ID, TITLE, CHUNK, SOURCE, CREATED_AT
    FROM MEMORY_DEMO.CORE.SERVICE_DOCS;

CREATE OR REPLACE SEMANTIC VIEW MEMORY_DEMO.CORE.TICKETS_ANALYTICS
  TABLES (
    tickets AS MEMORY_DEMO.CORE.SERVICE_TICKETS
      PRIMARY KEY (TICKET_ID)
      WITH SYNONYMS ('tickets', 'service tickets', 'work orders')
      COMMENT = 'One row per field service ticket'
  )
  FACTS (
    tickets.sentiment AS SENTIMENT_SCORE
      COMMENT = 'Sentiment of the ticket note, -1 very negative to 1 very positive'
  )
  DIMENSIONS (
    tickets.ticket_id AS TICKET_ID
      WITH SYNONYMS ('ticket number', 'ticket code')
      COMMENT = 'Ticket identifier',
    tickets.site AS SITE
      WITH SYNONYMS ('plant', 'location', 'depot')
      COMMENT = 'Site that raised the ticket',
    tickets.asset AS ASSET
      WITH SYNONYMS ('machine', 'equipment')
      COMMENT = 'Asset the ticket refers to',
    tickets.severity AS SEVERITY
      WITH SYNONYMS ('priority', 'criticality')
      COMMENT = 'Severity: low, medium, high or critical',
    tickets.status AS STATUS
      WITH SYNONYMS ('state')
      COMMENT = 'Status: open, in_progress or closed',
    tickets.run_id AS RUN_ID
      WITH SYNONYMS ('run', 'execution id')
      COMMENT = 'Identifier of the n8n run that wrote the row, seed for demo data',
    tickets.source AS SOURCE
      WITH SYNONYMS ('origin', 'writer')
      COMMENT = 'System that wrote the row',
    tickets.created_date AS TO_DATE(CREATED_AT)
      WITH SYNONYMS ('date', 'day', 'creation date')
      COMMENT = 'Date the ticket was created'
  )
  METRICS (
    tickets.ticket_count AS COUNT(tickets.ticket_id)
      WITH SYNONYMS ('number of tickets', 'how many tickets', 'volume')
      COMMENT = 'Number of tickets',
    tickets.avg_sentiment AS AVG(tickets.sentiment)
      WITH SYNONYMS ('average sentiment', 'mean sentiment')
      COMMENT = 'Average sentiment score',
    tickets.worst_sentiment AS MIN(tickets.sentiment)
      WITH SYNONYMS ('lowest sentiment', 'most negative')
      COMMENT = 'Most negative sentiment score'
  )
  COMMENT = 'Field service tickets for natural-language questions from n8n';
