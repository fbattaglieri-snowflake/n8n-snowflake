-- =============================================================================
-- 20_seed.sql
-- Deterministic synthetic seed rows for LLM_OPTIONS_DEMO.CORE.FLEET_OPPORTUNITIES.
-- Safe to re-run (truncates and reloads 10 synthetic rows).
-- =============================================================================

TRUNCATE TABLE LLM_OPTIONS_DEMO.CORE.FLEET_OPPORTUNITIES;

INSERT INTO LLM_OPTIONS_DEMO.CORE.FLEET_OPPORTUNITIES (
    OPPORTUNITY_ID, RANK, ASSET_MODEL, REGION, POTENTIAL_SCORE,
    REVENUE_POTENTIAL, NEXT_BEST_ACTION, OPERATING_HOURS,
    MAINTENANCE_PRIORITY, RECOMMENDED_ACTION, URGENCY_DAYS
)
VALUES
    ('OPP-001', 1,  'PRESS_A12',    'NORTH_ITALY',   97.5, 14800.0, 'offer_service_contract', 6420, 'high',   'Schedule 500h hydraulic return-filter & seal kit overhaul', 15),
    ('OPP-002', 2,  'CHILLER_C7',   'CENTRAL_ITALY', 95.0, 13950.0, 'offer_service_contract', 6180, 'high',   'Inspect shaft seal and run 30-minute refrigerant pressure test', 15),
    ('OPP-003', 3,  'PACKER_E5',    'SOUTH_GERMANY', 93.2, 12600.0, 'parts_upsell',           5890, 'high',   'Replace solid-state relay and calibrate sealing bar thermocouple', 20),
    ('OPP-004', 4,  'CONVEYOR_B3',  'EAST_FRANCE',   91.0, 11400.0, 'offer_service_contract', 5540, 'medium', 'Clean return rollers, square tail pulley, and tension belt to 320 N', 30),
    ('OPP-005', 5,  'ROBOT_ARM_D2', 'US_MIDWEST',    89.4, 10900.0, 'warranty_extension',     4920, 'medium', 'Fit high-force vacuum gripper and verify 0.6 bar drop protection', 30),
    ('OPP-006', 6,  'PRESS_A12',    'US_MIDWEST',    86.8,  9750.0, 'parts_upsell',           4610, 'medium', 'Measure static relief-valve pressure and replace rod seal kit', 45),
    ('OPP-007', 7,  'CHILLER_C7',   'NORTH_ITALY',   84.5,  8900.0, 'warranty_extension',     4120, 'medium', 'Flush condensate drain and verify compressor load cycle', 45),
    ('OPP-008', 8,  'PACKER_E5',    'IBERIA_HUB',    81.0,  7850.0, 'parts_upsell',           3780, 'low',    'Restock carton feeder wear kit ahead of Q4 peak shift', 60),
    ('OPP-009', 9,  'CONVEYOR_B3',  'BENELUX_DEPOT', 78.3,  6900.0, 'warranty_extension',     3340, 'low',    'Inspect transfer-point bearing housing and speed sensor', 60),
    ('OPP-010', 10, 'ROBOT_ARM_D2', 'CENTRAL_ITALY', 75.0,  6200.0, 'no_action',              2450, 'low',    'Nominal preventive calibration; next check at 3000 hours', 90);
