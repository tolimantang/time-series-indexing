-- Add astrological analysis columns to trading_opportunities table
-- This allows storing astrological data directly with each trading opportunity

-- Add columns for astrological analysis
ALTER TABLE trading_opportunities
ADD COLUMN IF NOT EXISTS entry_astro_description TEXT,
ADD COLUMN IF NOT EXISTS exit_astro_description TEXT,
ADD COLUMN IF NOT EXISTS entry_planetary_data JSONB,
ADD COLUMN IF NOT EXISTS exit_planetary_data JSONB,
ADD COLUMN IF NOT EXISTS astro_analysis_summary TEXT,
ADD COLUMN IF NOT EXISTS claude_analysis TEXT,
ADD COLUMN IF NOT EXISTS astrological_score DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS astro_analyzed_at TIMESTAMP WITH TIME ZONE;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_trading_opportunities_astro_analyzed
ON trading_opportunities(astro_analyzed_at)
WHERE astro_analyzed_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trading_opportunities_astro_score
ON trading_opportunities(astrological_score)
WHERE astrological_score IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN trading_opportunities.entry_astro_description IS 'Natural language description of astrological conditions at trade entry';
COMMENT ON COLUMN trading_opportunities.exit_astro_description IS 'Natural language description of astrological conditions at trade exit';
COMMENT ON COLUMN trading_opportunities.entry_planetary_data IS 'JSON data of planetary positions, aspects, lunar phase at entry';
COMMENT ON COLUMN trading_opportunities.exit_planetary_data IS 'JSON data of planetary positions, aspects, lunar phase at exit';
COMMENT ON COLUMN trading_opportunities.astro_analysis_summary IS 'Summary of astrological patterns for this trade';
COMMENT ON COLUMN trading_opportunities.claude_analysis IS 'Claude AI analysis of astrological significance';
COMMENT ON COLUMN trading_opportunities.astrological_score IS 'Composite score based on astrological favorability (0-100)';
COMMENT ON COLUMN trading_opportunities.astro_analyzed_at IS 'Timestamp when astrological analysis was performed';

-- Example query to find trades with specific astrological patterns
-- SELECT * FROM trading_opportunities
-- WHERE entry_astro_description ILIKE '%mars%jupiter%trine%'
-- AND profit_percent > 10
-- ORDER BY astrological_score DESC;