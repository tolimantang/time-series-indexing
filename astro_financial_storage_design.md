# Astro-Financial-Intermarket Storage Design

## Overview

This design supports querying across three domains:
1. **Astronomical**: Planetary positions, aspects, transits
2. **Financial News**: Fed actions, economic events, market sentiment
3. **Intermarket**: Price movements, correlations, volatility

## Storage Architecture

### PostgreSQL (Structured Data + Metadata)

```sql
-- Core daily record linking all domains
CREATE TABLE daily_records (
    date DATE PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    data_quality_score DECIMAL(3,2), -- 0.00-1.00
    has_astronomical_data BOOLEAN DEFAULT FALSE,
    has_financial_data BOOLEAN DEFAULT FALSE,
    has_market_data BOOLEAN DEFAULT FALSE
);

-- Astronomical data (structured)
CREATE TABLE astronomical_data (
    date DATE PRIMARY KEY REFERENCES daily_records(date),
    julian_day DECIMAL(12,6),

    -- Major planetary positions (degrees 0-360)
    sun_longitude DECIMAL(8,5),
    moon_longitude DECIMAL(8,5),
    mercury_longitude DECIMAL(8,5),
    venus_longitude DECIMAL(8,5),
    mars_longitude DECIMAL(8,5),
    jupiter_longitude DECIMAL(8,5),
    saturn_longitude DECIMAL(8,5),
    uranus_longitude DECIMAL(8,5),
    neptune_longitude DECIMAL(8,5),
    pluto_longitude DECIMAL(8,5),

    -- Key derived data
    lunar_phase DECIMAL(8,5),
    jupiter_sign VARCHAR(20),
    jupiter_degree_classification VARCHAR(10), -- 'early', 'middle', 'late'
    moon_sign VARCHAR(20),

    -- Major aspects (JSON for flexibility)
    major_conjunctions JSONB, -- [{"planets": ["saturn", "neptune"], "orb": 3.4, "exactness": 0.58}]
    all_aspects JSONB,

    -- Raw data reference
    full_astro_data JSONB -- Complete data from astroEncoder
);

-- Financial news data (structured)
CREATE TABLE financial_news_data (
    date DATE PRIMARY KEY REFERENCES daily_records(date),

    -- Fed activity
    has_fed_events BOOLEAN DEFAULT FALSE,
    fed_action_type VARCHAR(50), -- 'rate_hike', 'rate_cut', 'hold', 'speech', NULL
    fed_rate_change DECIMAL(4,2), -- basis points
    fed_summary TEXT,

    -- Economic data
    major_economic_releases JSONB, -- [{"name": "CPI", "actual": "3.2%", "impact": "high"}]
    economic_surprise_index DECIMAL(5,2), -- positive = beats expectations

    -- Market regime indicators
    market_regime VARCHAR(20), -- 'risk_on', 'risk_off', 'high_volatility', 'low_volatility'
    volatility_regime VARCHAR(20), -- 'low', 'normal', 'high', 'extreme'

    -- Text summaries
    daily_summary TEXT,
    combined_summary TEXT, -- For embedding/search

    -- Raw data reference
    full_news_data JSONB
);

-- Intermarket/price data
CREATE TABLE market_data (
    date DATE REFERENCES daily_records(date),
    symbol VARCHAR(20),

    -- OHLC data
    open_price DECIMAL(12,6),
    high_price DECIMAL(12,6),
    low_price DECIMAL(12,6),
    close_price DECIMAL(12,6),
    volume BIGINT,

    -- Derived metrics
    daily_return DECIMAL(8,5), -- percentage
    volatility_20d DECIMAL(8,5), -- 20-day rolling volatility
    relative_strength DECIMAL(8,5), -- vs benchmark

    -- Classification
    asset_class VARCHAR(20), -- 'equity', 'currency', 'commodity', 'fixed_income'

    PRIMARY KEY (date, symbol)
);

-- Intermarket correlations (pre-computed)
CREATE TABLE intermarket_correlations (
    date DATE REFERENCES daily_records(date),
    symbol1 VARCHAR(20),
    symbol2 VARCHAR(20),
    correlation_30d DECIMAL(6,5), -- 30-day rolling correlation
    correlation_strength VARCHAR(20), -- 'strong_positive', 'weak_negative', etc.

    PRIMARY KEY (date, symbol1, symbol2)
);

-- Pattern detection results
CREATE TABLE detected_patterns (
    id SERIAL PRIMARY KEY,
    date_start DATE,
    date_end DATE,
    pattern_type VARCHAR(50), -- 'astro_conjunction', 'fed_cycle', 'volatility_spike'
    pattern_description TEXT,
    confidence_score DECIMAL(3,2),
    related_symbols TEXT[], -- Array of affected symbols
    pattern_data JSONB
);

-- Query results cache for performance
CREATE TABLE pattern_correlations (
    id SERIAL PRIMARY KEY,
    pattern_hash VARCHAR(64), -- Hash of query parameters
    query_description TEXT,
    date_ranges JSONB, -- Array of date ranges matching pattern
    market_effects JSONB, -- Statistical summary of market effects
    sample_size INTEGER,
    statistical_significance DECIMAL(4,3),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### ChromaDB (Semantic Search Collections)

```python
import chromadb

client = chromadb.Client()

# Collection 1: Daily combined summaries
daily_summaries = client.create_collection(
    name="daily_astro_financial_summaries",
    metadata={
        "description": "Combined astronomical + financial summaries for semantic similarity search"
    }
)

# Collection 2: Astronomical patterns only
astro_patterns = client.create_collection(
    name="astronomical_patterns",
    metadata={
        "description": "Pure astronomical pattern descriptions for astro-specific queries"
    }
)

# Collection 3: Financial events only
financial_events = client.create_collection(
    name="financial_events",
    metadata={
        "description": "Pure financial/economic event descriptions"
    }
)

# Collection 4: Market regime descriptions
market_regimes = client.create_collection(
    name="market_regimes",
    metadata={
        "description": "Market condition and regime descriptions for similarity matching"
    }
)
```

## Data Flow & Storage Process

### 1. Daily Data Ingestion

```python
def store_daily_data(date):
    # 1. Get all three data types
    astro_data = astro_encoder.encode_date(date)
    news_data = news_encoder.encode_date(date)
    market_data = get_market_data(date)  # Your market API

    # 2. Store in PostgreSQL (structured)
    store_postgresql_data(date, astro_data, news_data, market_data)

    # 3. Create embeddings and store in ChromaDB
    store_chromadb_embeddings(date, astro_data, news_data, market_data)

def store_postgresql_data(date, astro_data, news_data, market_data):
    # Insert core record
    cursor.execute("""
        INSERT INTO daily_records (date, data_quality_score, has_astronomical_data, has_financial_data, has_market_data)
        VALUES (%s, %s, %s, %s, %s)
    """, (date, calculate_quality_score(astro_data, news_data, market_data), True, True, True))

    # Insert astronomical data
    cursor.execute("""
        INSERT INTO astronomical_data (
            date, julian_day, sun_longitude, moon_longitude, ...,
            jupiter_sign, lunar_phase, major_conjunctions, full_astro_data
        ) VALUES (%s, %s, %s, %s, ..., %s, %s, %s, %s)
    """, (date, astro_data.julian_day, astro_data.positions['sun'].longitude, ...))

    # Insert financial data
    cursor.execute("""
        INSERT INTO financial_news_data (
            date, has_fed_events, fed_summary, market_regime, combined_summary, full_news_data
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """, (date, len(news_data.fed_events) > 0, news_data.fed_summary, ...))

    # Insert market data for each symbol
    for symbol, data in market_data.items():
        cursor.execute("""
            INSERT INTO market_data (date, symbol, close_price, daily_return, ...)
            VALUES (%s, %s, %s, %s, ...)
        """, (date, symbol, data.close, data.daily_return, ...))

def store_chromadb_embeddings(date, astro_data, news_data, market_data):
    date_str = date.strftime('%Y-%m-%d')

    # 1. Combined summary embedding
    combined_text = create_combined_summary(astro_data, news_data, market_data)
    daily_summaries.add(
        documents=[combined_text],
        metadatas=[{
            'date': date_str,
            'has_conjunctions': has_major_conjunctions(astro_data),
            'has_fed_events': len(news_data.fed_events) > 0,
            'market_regime': news_data.market_regime,
            'vix_level': get_vix_level(market_data)
        }],
        ids=[f"daily_{date_str}"]
    )

    # 2. Pure astronomical pattern
    astro_text = create_astro_summary(astro_data)
    astro_patterns.add(
        documents=[astro_text],
        metadatas=[{
            'date': date_str,
            'jupiter_sign': astro_data.positions['jupiter'].sign,
            'major_aspects': len([a for a in astro_data.aspects if a.orb <= 3.0])
        }],
        ids=[f"astro_{date_str}"]
    )

    # 3. Pure financial events
    financial_text = news_data.get_combined_summary()
    financial_events.add(
        documents=[financial_text],
        metadatas=[{
            'date': date_str,
            'fed_events': len(news_data.fed_events),
            'economic_events': len(news_data.economic_data)
        }],
        ids=[f"financial_{date_str}"]
    )

def create_combined_summary(astro_data, news_data, market_data):
    """Create unified text combining all three domains."""
    parts = []

    # Astronomical component
    conjunctions = [a for a in astro_data.aspects if a.aspect_type == 'conjunction' and a.orb <= 5]
    if conjunctions:
        conj_text = ", ".join([f"{c.planet1}-{c.planet2}" for c in conjunctions])
        parts.append(f"Astronomical: {conj_text} conjunctions")

    jupiter_pos = astro_data.positions['jupiter']
    parts.append(f"Jupiter in {jupiter_pos.degree_classification} {jupiter_pos.sign}")

    moon_pos = astro_data.positions['moon']
    parts.append(f"Moon in {moon_pos.sign}")

    # Financial component
    if news_data.fed_events:
        parts.append(f"Fed: {news_data.fed_summary}")

    if news_data.market_regime:
        parts.append(f"Market regime: {news_data.market_regime}")

    # Market component
    spy_return = market_data.get('SPY', {}).get('daily_return', 0)
    vix_level = market_data.get('VIX', {}).get('close', 15)
    oil_return = market_data.get('USO', {}).get('daily_return', 0)
    eurusd_return = market_data.get('EURUSD', {}).get('daily_return', 0)

    parts.append(f"Markets: SPY {spy_return:+.1f}%, VIX {vix_level:.1f}")
    parts.append(f"Oil {oil_return:+.1f}%, EUR/USD {eurusd_return:+.1f}%")

    return " | ".join(parts)
```

## Query System Design

### Query Types & Implementation

```python
class AstroFinancialQuerySystem:
    def __init__(self):
        self.chroma_client = chromadb.Client()
        self.pg_connection = psycopg2.connect(...)

    def query_saturn_neptune_effects(self, max_orb=8.0, lookback_days=30):
        """Query: What happens to markets during Saturn-Neptune conjunctions?"""

        # 1. Find dates with Saturn-Neptune conjunctions (PostgreSQL)
        cursor = self.pg_connection.cursor()
        cursor.execute("""
            SELECT date, major_conjunctions
            FROM astronomical_data
            WHERE major_conjunctions @> '[{"planets": ["saturn", "neptune"]}]'
              AND (major_conjunctions->0->>'orb')::float <= %s
        """, (max_orb,))

        conjunction_dates = cursor.fetchall()

        # 2. Get market data for those periods + lookback/lookforward
        market_effects = {}
        for date, _ in conjunction_dates:
            start_date = date - timedelta(days=lookback_days)
            end_date = date + timedelta(days=lookback_days)

            cursor.execute("""
                SELECT symbol, AVG(daily_return) as avg_return, STDDEV(daily_return) as volatility
                FROM market_data
                WHERE date BETWEEN %s AND %s
                  AND symbol IN ('SPY', 'EURUSD', 'USO', 'UNH')
                GROUP BY symbol
            """, (start_date, end_date))

            market_effects[date] = cursor.fetchall()

        # 3. Get news context via ChromaDB similarity search
        date_strings = [d.strftime('%Y-%m-%d') for d, _ in conjunction_dates]
        news_context = []

        for date_str in date_strings:
            results = self.chroma_client.get_collection("financial_events").get(
                ids=[f"financial_{date_str}"]
            )
            news_context.extend(results['documents'])

        return {
            'conjunction_periods': conjunction_dates,
            'market_effects': market_effects,
            'news_context': news_context,
            'statistical_summary': self._calculate_statistics(market_effects)
        }

    def query_similar_periods(self, query_text, n_results=10):
        """Query: Find periods similar to 'Fed hiking cycle with tech weakness'"""

        # Use ChromaDB similarity search on combined summaries
        results = self.chroma_client.get_collection("daily_astro_financial_summaries").query(
            query_texts=[query_text],
            n_results=n_results,
            include=['metadatas', 'documents', 'distances']
        )

        # Get detailed data from PostgreSQL
        similar_periods = []
        for i, metadata in enumerate(results['metadatas'][0]):
            date = metadata['date']

            # Get full context from PostgreSQL
            cursor = self.pg_connection.cursor()
            cursor.execute("""
                SELECT
                    dr.date,
                    ad.major_conjunctions,
                    fnd.fed_summary,
                    fnd.market_regime,
                    array_agg(md.symbol || ': ' || md.daily_return::text) as market_moves
                FROM daily_records dr
                LEFT JOIN astronomical_data ad ON dr.date = ad.date
                LEFT JOIN financial_news_data fnd ON dr.date = fnd.date
                LEFT JOIN market_data md ON dr.date = md.date
                WHERE dr.date = %s
                GROUP BY dr.date, ad.major_conjunctions, fnd.fed_summary, fnd.market_regime
            """, (date,))

            detailed_data = cursor.fetchone()
            similar_periods.append({
                'date': date,
                'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                'summary': results['documents'][0][i],
                'detailed_data': detailed_data
            })

        return similar_periods

    def query_jupiter_cancer_moon_gemini_effects(self):
        """Query: Jupiter in late Cancer + Moon about to enter Gemini effects"""

        cursor = self.pg_connection.cursor()
        cursor.execute("""
            SELECT
                dr.date,
                ad.jupiter_sign,
                ad.jupiter_degree_classification,
                ad.moon_sign,
                fnd.market_regime,
                array_agg(
                    CASE
                        WHEN md.symbol IN ('EURUSD', 'USO', 'UNH')
                        THEN md.symbol || ': ' || md.daily_return::text
                    END
                ) as target_assets
            FROM daily_records dr
            JOIN astronomical_data ad ON dr.date = ad.date
            LEFT JOIN financial_news_data fnd ON dr.date = fnd.date
            LEFT JOIN market_data md ON dr.date = md.date
            WHERE ad.jupiter_sign = 'cancer'
              AND ad.jupiter_degree_classification = 'late'
              AND ad.moon_sign IN ('taurus', 'gemini') -- Moon in Taurus about to enter Gemini
            GROUP BY dr.date, ad.jupiter_sign, ad.jupiter_degree_classification,
                     ad.moon_sign, fnd.market_regime
            ORDER BY dr.date
        """)

        matching_periods = cursor.fetchall()

        # Calculate statistical effects
        effects_summary = self._analyze_market_effects(matching_periods, ['EURUSD', 'USO', 'UNH'])

        return {
            'matching_periods': matching_periods,
            'market_effects': effects_summary,
            'sample_size': len(matching_periods),
            'confidence_level': self._calculate_confidence(matching_periods)
        }
```

## Benefits of This Design

### ✅ Supports All Query Types
1. **Structured queries**: Fast PostgreSQL joins for specific criteria
2. **Similarity search**: ChromaDB for "find similar" queries
3. **Multi-modal**: Combine astronomical, financial, and market data
4. **Statistical analysis**: Pre-computed correlations and effects

### ✅ Scalable & Performant
- PostgreSQL handles 50 years of daily data easily (~18K records)
- ChromaDB provides sub-second similarity search
- Indexed on common query patterns
- Caching layer for expensive correlation calculations

### ✅ Flexible & Extensible
- Easy to add new astronomical indicators
- Simple to expand market coverage
- ChromaDB allows natural language queries
- JSON fields provide schema flexibility

This design gives you the foundation to answer questions like:
- "Show me all Saturn-Neptune conjunctions when Fed was hiking and EUR/USD was volatile"
- "Find periods similar to March 2020 crisis"
- "What typically happens to oil when Jupiter enters Cancer during low volatility regimes?"

Ready to implement the storage layer?