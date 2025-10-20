-- AstroFinancial Database Schema
-- Migration 001: Initial schema for users and search history

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    subscription_tier VARCHAR(50) DEFAULT 'basic' CHECK (subscription_tier IN ('basic', 'premium', 'enterprise')),
    api_quota_daily INTEGER DEFAULT 100,
    api_calls_today INTEGER DEFAULT 0,
    quota_reset_date DATE DEFAULT CURRENT_DATE
);

-- Search history table
CREATE TABLE search_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    query_type VARCHAR(50) NOT NULL CHECK (query_type IN ('semantic_search', 'pattern_analysis', 'structured_query')),
    query_params JSONB NOT NULL DEFAULT '{}',
    results JSONB NOT NULL DEFAULT '{}',
    results_count INTEGER DEFAULT 0,
    execution_time_ms REAL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_saved BOOLEAN DEFAULT false,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[]
);

-- User sessions table (for JWT token management)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    jwt_token_id VARCHAR(255) NOT NULL, -- jti claim from JWT
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT false,
    user_agent TEXT,
    ip_address INET
);

-- Performance indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;
CREATE INDEX idx_search_history_user_id ON search_history(user_id);
CREATE INDEX idx_search_history_created_at ON search_history(created_at DESC);
CREATE INDEX idx_search_history_query_type ON search_history(query_type);
CREATE INDEX idx_search_history_user_time ON search_history(user_id, created_at DESC);

-- JSONB indexes for flexible querying
CREATE INDEX idx_search_history_query_params_gin ON search_history USING GIN (query_params);
CREATE INDEX idx_search_history_results_gin ON search_history USING GIN (results);

-- Session management indexes
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token_id ON user_sessions(jwt_token_id);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to reset daily API calls
CREATE OR REPLACE FUNCTION reset_daily_api_calls()
RETURNS void AS $$
BEGIN
    UPDATE users
    SET api_calls_today = 0,
        quota_reset_date = CURRENT_DATE
    WHERE quota_reset_date < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- Create admin user (password: admin123 - CHANGE IN PRODUCTION!)
INSERT INTO users (email, password_hash, full_name, is_admin, subscription_tier, api_quota_daily)
VALUES (
    'admin@astrofinancial.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LetyOmUOsQ8qAOzgK', -- admin123
    'System Administrator',
    true,
    'enterprise',
    10000
);

-- Create sample user (password: user123 - CHANGE IN PRODUCTION!)
INSERT INTO users (email, password_hash, full_name, subscription_tier)
VALUES (
    'demo@astrofinancial.com',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', -- user123
    'Demo User',
    'premium'
);

-- Grant necessary permissions (adjust for your PostgreSQL setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO astrofinancial_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO astrofinancial_app;