USE ROLE <% deploy_role %>;
USE DATABASE <% database %>;
USE SCHEMA <% schema %>;
USE WAREHOUSE <% warehouse %>;

CREATE SERVICE IF NOT EXISTS CORTEX_PROXY_SERVICE
  IN COMPUTE POOL <% compute_pool %>
  FROM @N8N_CONFIG
  SPECIFICATION_TEMPLATE_FILE = 'cortex-proxy.service.yaml'
  USING (
    database => '<% database %>',
    schema => '<% schema %>',
    proxy_image_repository => '<% proxy_image_repository %>',
    image_tag => '<% image_tag %>'
  )
  AUTO_RESUME = TRUE
  MIN_INSTANCES = 1
  MAX_INSTANCES = 1
  QUERY_WAREHOUSE = <% warehouse %>
  COMMENT = 'Private Cortex and Snowflake SQL API compatibility proxy';

ALTER SERVICE CORTEX_PROXY_SERVICE
  FROM @N8N_CONFIG
  SPECIFICATION_TEMPLATE_FILE = 'cortex-proxy.service.yaml'
  USING (
    database => '<% database %>',
    schema => '<% schema %>',
    proxy_image_repository => '<% proxy_image_repository %>',
    image_tag => '<% image_tag %>'
  );

CREATE SERVICE IF NOT EXISTS N8N_SERVICE
  IN COMPUTE POOL <% compute_pool %>
  FROM @N8N_CONFIG
  SPECIFICATION_TEMPLATE_FILE = 'n8n.service.yaml'
  USING (
    database => '<% database %>',
    schema => '<% schema %>',
    n8n_image_repository => '<% n8n_image_repository %>',
    image_tag => '<% image_tag %>',
    postgres_host => '<% postgres_host %>',
    postgres_database => '<% postgres_database %>'
  )
  AUTO_RESUME = TRUE
  MIN_INSTANCES = 1
  MAX_INSTANCES = 1
  EXTERNAL_ACCESS_INTEGRATIONS = (<% egress_integration %>)
  QUERY_WAREHOUSE = <% warehouse %>
  COMMENT = 'n8n Community Edition on Snowpark Container Services';

ALTER SERVICE N8N_SERVICE
  FROM @N8N_CONFIG
  SPECIFICATION_TEMPLATE_FILE = 'n8n.service.yaml'
  USING (
    database => '<% database %>',
    schema => '<% schema %>',
    n8n_image_repository => '<% n8n_image_repository %>',
    image_tag => '<% image_tag %>',
    postgres_host => '<% postgres_host %>',
    postgres_database => '<% postgres_database %>'
  );

