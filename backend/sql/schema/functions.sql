-- Ground Truth Function Definitions
-- This file represents the CURRENT desired state of all functions and triggers

-- Updated At Trigger Function
-- ===========================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

COMMENT ON FUNCTION update_updated_at_column() IS 'Automatically updates the updated_at column when a row is modified';

-- Triggers for Updated At
-- =======================

-- Lunar patterns trigger
DROP TRIGGER IF EXISTS update_lunar_patterns_updated_at ON lunar_patterns;
CREATE TRIGGER update_lunar_patterns_updated_at
    BEFORE UPDATE ON lunar_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Astrological insights trigger
DROP TRIGGER IF EXISTS update_astrological_insights_updated_at ON astrological_insights;
CREATE TRIGGER update_astrological_insights_updated_at
    BEFORE UPDATE ON astrological_insights
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Utility Functions
-- =================

CREATE OR REPLACE FUNCTION get_lunar_phase_name(phase_angle DOUBLE PRECISION)
RETURNS VARCHAR(50) AS $$
BEGIN
    CASE
        WHEN phase_angle >= 0 AND phase_angle < 45 THEN RETURN 'New Moon';
        WHEN phase_angle >= 45 AND phase_angle < 90 THEN RETURN 'Waxing Crescent';
        WHEN phase_angle >= 90 AND phase_angle < 135 THEN RETURN 'First Quarter';
        WHEN phase_angle >= 135 AND phase_angle < 180 THEN RETURN 'Waxing Gibbous';
        WHEN phase_angle >= 180 AND phase_angle < 225 THEN RETURN 'Full Moon';
        WHEN phase_angle >= 225 AND phase_angle < 270 THEN RETURN 'Waning Gibbous';
        WHEN phase_angle >= 270 AND phase_angle < 315 THEN RETURN 'Last Quarter';
        WHEN phase_angle >= 315 AND phase_angle < 360 THEN RETURN 'Waning Crescent';
        ELSE RETURN 'Unknown';
    END CASE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_lunar_phase_name(DOUBLE PRECISION) IS 'Converts lunar phase angle to human-readable phase name';

CREATE OR REPLACE FUNCTION calculate_pattern_expected_return(
    accuracy_rate DECIMAL(5,3),
    avg_up_move DECIMAL(8,4),
    avg_down_move DECIMAL(8,4),
    prediction VARCHAR(10)
)
RETURNS DECIMAL(8,4) AS $$
BEGIN
    IF prediction = 'up' THEN
        RETURN accuracy_rate * avg_up_move;
    ELSIF prediction = 'down' THEN
        RETURN accuracy_rate * ABS(avg_down_move);
    ELSE
        RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_pattern_expected_return(DECIMAL, DECIMAL, DECIMAL, VARCHAR) IS 'Calculates expected return for a lunar pattern based on accuracy and historical moves';