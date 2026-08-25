USE ROLE <% deploy_role %>;

-- This file is rendered with action=suspend or action=resume by the workflow.
-- The shell workflow selects explicit statements instead of templating arbitrary SQL.
SELECT 'Use .github/workflows/operate.yml for ordered stack operations.' AS instruction;

