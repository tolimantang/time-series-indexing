# SQL Schema Management

This directory contains SQL migrations, schemas, and scripts for the AstroFinancial database.

## Directory Structure

```
sql/
├── migrations/          # Database migration files
├── schemas/            # Schema definitions and documentation
├── scripts/            # Management and utility scripts
└── README.md           # This file
```

## Migrations

Migrations are located in `migrations/` and follow the naming convention:
- `001_initial_schema.sql` - Initial database setup
- `002_add_market_data.sql` - Market data tables for P&L calculations

### Running Migrations

Use the migration runner script:

```bash
# Run all pending migrations
python sql/scripts/run_migration.py run

# Check migration status
python sql/scripts/run_migration.py status
```

### Environment Variables

Set these environment variables for database connection:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=astrofinancial
export DB_USER=postgres
export DB_PASSWORD=your_password
```

## Market Data Schema

The `market_data` table stores OHLCV data for financial analysis:

```sql
CREATE TABLE market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(12,4) NOT NULL,
    high_price DECIMAL(12,4) NOT NULL,
    low_price DECIMAL(12,4) NOT NULL,
    close_price DECIMAL(12,4) NOT NULL,
    adjusted_close DECIMAL(12,4),
    volume BIGINT NOT NULL DEFAULT 0,
    daily_return DECIMAL(8,6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, trade_date)
);
```

## Portfolio P&L Tracking

The `portfolio_positions` table tracks user positions for P&L calculations:

```sql
CREATE TABLE portfolio_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    symbol VARCHAR(10) NOT NULL,
    entry_date DATE NOT NULL,
    exit_date DATE,
    entry_price DECIMAL(12,4) NOT NULL,
    exit_price DECIMAL(12,4),
    quantity DECIMAL(12,4) NOT NULL,
    position_type VARCHAR(10) CHECK (position_type IN ('long', 'short')),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'partial'))
);
```

## P&L View

The `portfolio_pnl` view provides easy P&L calculations:

```sql
-- Get P&L for all positions
SELECT * FROM portfolio_pnl WHERE user_id = 'your-user-id';

-- Get P&L for specific symbol
SELECT * FROM portfolio_pnl WHERE symbol = 'SPX' AND user_id = 'your-user-id';
```

## Market Encoder Integration

The `MarketEncoder` class automatically stores market data in PostgreSQL:

```python
from market_encoder import MarketEncoder

# Initialize with database config
encoder = MarketEncoder(db_config={
    'host': 'localhost',
    'port': '5432',
    'database': 'astrofinancial',
    'user': 'postgres',
    'password': 'password'
})

# Calculate hypothetical P&L
pnl = encoder.calculate_hypothetical_pnl(
    symbol='SPX',
    entry_date='2024-01-01',
    exit_date='2024-01-31',
    quantity=100,
    position_type='long'
)
```

## Data Flow

1. **ChromaDB**: Stores market narratives and embeddings for semantic search
2. **PostgreSQL**: Stores structured market data for P&L calculations and time-series analysis

This dual approach provides:
- Fast semantic search capabilities (ChromaDB)
- Robust financial calculations and queries (PostgreSQL)
- Data consistency and integrity for financial analysis