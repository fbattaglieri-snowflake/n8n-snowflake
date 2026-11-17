-- Grant runtime access on the deployed Cortex Agent to MEMORY_DEMO_ROLE.
-- Run after deploying 40_agent.yaml.

GRANT USAGE ON AGENT MEMORY_DEMO.CORE.MEMORY_DEMO_AGENT TO ROLE MEMORY_DEMO_ROLE;
