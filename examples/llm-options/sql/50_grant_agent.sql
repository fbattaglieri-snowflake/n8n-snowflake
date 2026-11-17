-- Grant runtime access on the deployed Cortex Agent to N8N_DEMO_ROLE.
-- Run after deploying 40_agent.yaml.

GRANT USAGE ON AGENT LLM_OPTIONS_DEMO.CORE.PLATFORM_DOCS_AGENT TO ROLE N8N_DEMO_ROLE;
