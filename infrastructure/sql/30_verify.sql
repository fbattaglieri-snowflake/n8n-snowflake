USE ROLE <% deploy_role %>;

SHOW SERVICE CONTAINERS IN SERVICE <% database %>.<% schema %>.CORTEX_PROXY_SERVICE;
SHOW SERVICE CONTAINERS IN SERVICE <% database %>.<% schema %>.N8N_SERVICE;
SHOW ENDPOINTS IN SERVICE <% database %>.<% schema %>.N8N_SERVICE;

