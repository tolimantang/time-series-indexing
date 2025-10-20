# Financial Pattern Library Setup

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
# Core dependencies
pip install yfinance pandas numpy

# Chronos (for embeddings)
pip install chronos-forecasting torch

# Optional: if you don't have torch, it will use dummy embeddings
```

### 2. Build Pattern Library
```bash
# From project root directory
python run_pattern_builder.py
```

This will:
- ✅ Download historical market data
- ✅ Create pattern embeddings using Chronos
- ✅ Save pattern library to `patterns/` directory
- ✅ Test the query interface

### 3. Expected Output
```
🚀 Financial Pattern Builder & Tester
==================================================

📊 Step 1: Building Pattern Library
------------------------------
Using curated fed_rate_hikes dates (replace with LLM call)
Getting SPY data for 17 dates...
  Progress: 10/17
  ✅ Successfully created 16 segments
Loading Chronos model...
Creating embeddings for 16 segments...
  ✅ Created average embedding with shape: (512,)

✅ Built 3 patterns successfully!
```

## What Gets Created

### Pattern Files
```
patterns/
└── pattern_library_spy.json    # Pattern embeddings and metadata
```

### Pattern Types Built
1. **fed_rate_hikes** - Federal Reserve rate increase dates
2. **market_crashes** - Major market decline days
3. **vix_spikes** - Volatility spike periods

## Using the Patterns

### Basic Query Interface
```python
from tsindexing.patterns.pattern_query import PatternQueryInterface

# Initialize
query_interface = PatternQueryInterface()

# Query patterns
result = query_interface.query_pattern("What happens during Fed rate hikes?")

if result["success"]:
    embedding = result["pattern_embedding"]  # 512D Chronos embedding
    pattern_type = result["pattern_type"]    # "fed_rate_hikes"

    # Use with your vector search system
    similar_periods = your_index.search(embedding, top_k=10)
```

### Integration with Your Existing System
```python
# In your main query handler
from tsindexing.patterns.pattern_query import PatternQueryInterface

query_interface = PatternQueryInterface()

def handle_text_query(user_query):
    # Try to convert text to pattern embedding
    result = query_interface.query_pattern(user_query)

    if result["success"]:
        # Use pattern embedding for similarity search
        pattern_embedding = result["pattern_embedding"]
        similar_periods = your_chronos_index.search(pattern_embedding, top_k=10)
        return similar_periods
    else:
        return f"Pattern not found: {result['error']}"

# Example usage
similar = handle_text_query("What happens during market crashes?")
```

## Supported Queries

### Fed Rate Patterns
- "Fed rate hikes"
- "Federal Reserve policy"
- "Interest rate increases"
- "FOMC decisions"
- "Monetary tightening"

### Market Crash Patterns
- "Market crashes"
- "Stock declines"
- "Market selloffs"
- "Financial crisis"
- "Bear market"

### Volatility Patterns
- "VIX spikes"
- "Volatility surges"
- "Market fear"
- "Panic selling"

## Troubleshooting

### Missing Dependencies
```bash
# Error: chronos not found
pip install chronos-forecasting torch

# Error: yfinance not found
pip install yfinance

# Error: pandas/numpy not found
pip install pandas numpy
```

### No Pattern Data
```bash
# If patterns directory is empty, run:
python run_pattern_builder.py

# Or manually:
python -m tsindexing.patterns.llm_pattern_builder
```

### Chronos Not Available
If Chronos installation fails, the system will use dummy embeddings for testing. The pattern structure will work, but embeddings won't be meaningful.

## Expanding the Pattern Library

### Adding New Pattern Types
Edit `src/tsindexing/patterns/llm_pattern_builder.py`:

```python
# Add to llm_prompts dictionary
"earnings_beats": """
List dates when major tech companies beat earnings expectations significantly.
Format: YYYY-MM-DD (one per line)
..."""

# Add to curated_patterns dictionary
"earnings_beats": [
    "2021-01-27",  # AAPL beats
    "2021-04-28",  # GOOGL beats
    # ... more dates
]
```

### Adding New Query Triggers
Edit `src/tsindexing/patterns/pattern_query.py`:

```python
# Add to text_to_pattern_map
"earnings": "earnings_beats",
"beat estimates": "earnings_beats",
"earnings surprise": "earnings_beats"
```

## Performance Notes

- **Pattern Building**: ~2-5 minutes (downloads data + creates embeddings)
- **Query Speed**: Instant (patterns are pre-computed)
- **Memory Usage**: ~100MB (loads Chronos model once)
- **Storage**: ~1MB per pattern library file

## Next Steps

1. **Test Integration**: Use patterns with your existing Chronos vector search
2. **Add LLM Integration**: Replace curated dates with actual LLM API calls
3. **Expand Patterns**: Add more financial event types
4. **Validate Results**: Compare pattern matches with expected historical behavior