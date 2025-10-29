-- Create financial events table for dual storage with ChromaDB
-- This table stores structured financial events for time-range queries, aggregations, and analysis

CREATE TABLE financial_events (
    id SERIAL PRIMARY KEY,

    -- Event identification
    event_id VARCHAR(255) NOT NULL UNIQUE,  -- Same ID as ChromaDB for linking
    event_date DATE NOT NULL,               -- Event date for fast time queries
    event_datetime TIMESTAMP WITH TIME ZONE NOT NULL, -- Full timestamp with timezone

    -- Event classification
    source VARCHAR(50) NOT NULL,            -- 'fred', 'news', 'sec', etc.
    event_type VARCHAR(100) NOT NULL,       -- 'fed_decision', 'employment_data', etc.
    importance VARCHAR(20) NOT NULL,        -- 'high', 'medium', 'low'

    -- Event content
    title VARCHAR(500) NOT NULL,            -- Human-readable title
    description TEXT,                       -- Full description
    document_text TEXT,                     -- Full document text for search

    -- Event data (FRED specific but can extend)
    series_id VARCHAR(50),                  -- FRED series ID (if applicable)
    value DECIMAL(15,6),                    -- Numeric value (rate, index, etc.)
    previous_value DECIMAL(15,6),           -- Previous value for change calculation
    change_amount DECIMAL(15,6),            -- Absolute change
    change_percent DECIMAL(8,4),            -- Percentage change

    -- Market context
    market_impact VARCHAR(50),              -- Expected market impact
    sector_impact JSONB,                    -- Impact by sector (if applicable)
    keywords TEXT[],                        -- Searchable keywords

    -- Metadata for analytics
    metadata JSONB,                         -- Flexible metadata storage
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT financial_events_importance_check CHECK (importance IN ('high', 'medium', 'low')),
    CONSTRAINT financial_events_source_check CHECK (source IN ('fred', 'news', 'sec', 'earnings', 'fed', 'bls', 'census'))
);

-- Indexes for fast queries
CREATE INDEX idx_financial_events_date ON financial_events(event_date);
CREATE INDEX idx_financial_events_datetime ON financial_events(event_datetime);
CREATE INDEX idx_financial_events_source_type ON financial_events(source, event_type);
CREATE INDEX idx_financial_events_importance ON financial_events(importance);
CREATE INDEX idx_financial_events_series ON financial_events(series_id) WHERE series_id IS NOT NULL;
CREATE INDEX idx_financial_events_keywords ON financial_events USING GIN(keywords);
CREATE INDEX idx_financial_events_metadata ON financial_events USING GIN(metadata);

-- Index for time range queries (most common use case)
CREATE INDEX idx_financial_events_date_importance ON financial_events(event_date, importance);
CREATE INDEX idx_financial_events_type_date ON financial_events(event_type, event_date);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_financial_events_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_financial_events_updated_at
    BEFORE UPDATE ON financial_events
    FOR EACH ROW
    EXECUTE FUNCTION update_financial_events_updated_at();

-- Add to tables.sql reference
COMMENT ON TABLE financial_events IS 'Financial events storage for time-range queries and structured analysis. Complements ChromaDB semantic search.';
COMMENT ON COLUMN financial_events.event_id IS 'Unique identifier matching ChromaDB document ID for cross-referencing';
COMMENT ON COLUMN financial_events.metadata IS 'Flexible JSONB storage for source-specific data and future extensibility';
COMMENT ON COLUMN financial_events.keywords IS 'Array of searchable keywords for full-text search capabilities';