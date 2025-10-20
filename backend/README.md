# Time Series Indexing Backend

A Python-based system for indexing and encoding financial time series data.

## 🏗️ Project Structure

```
backend/
├── pyproject.toml                  # Python project configuration
├── requirements.txt                # Legacy requirements (kept for compatibility)
│
├── src/                            # Python source code
│   ├── market_encoder/             # Market data encoding package
│   │   ├── core/                   # Core business logic
│   │   │   ├── encoder.py          # Base market encoder
│   │   │   ├── multi_encoder.py    # Multi-security encoder
│   │   │   ├── simple_encoder.py   # Simplified daily encoder
│   │   │   └── text_generator.py   # Market narrative generation
│   │   ├── data/                   # Data sources
│   │   │   └── data_sources.py     # Yahoo Finance & Alpha Vantage
│   │   ├── signals/                # Signal generation
│   │   │   └── signal_generator.py # Technical indicators
│   │   ├── storage/                # Storage backends
│   │   └── config/                 # Configuration
│   │       └── config.py           # Configuration loader
│   │
│   └── shared/                     # Shared utilities (future)
│       └── __init__.py
│
├── scripts/                        # CLI entry points
│   ├── daily_market_encoding.py    # Full market encoder with indicators
│   ├── simple_daily_encoding.py    # Simple daily price encoder
│   └── test_market_encoder.py      # Local testing script
│
├── config/                         # Configuration files
│   ├── securities.yaml             # Securities to encode
│   └── securities_simple.yaml      # Simplified config
│
├── deploy/                         # Deployment configurations
│   ├── k8s/                        # Kubernetes manifests
│   │   ├── market-encoder/         # Market encoder specific
│   │   └── shared/                 # Shared infrastructure
│   └── docker/                     # Docker configurations
│       └── market-encoder.Dockerfile
│
└── sql/                           # Database related
    ├── migrations/                # Database migrations
    └── scripts/                   # Database utilities
```

## 🚀 Quick Start

### Installation

```bash
# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### Usage

```bash
# Run simple daily encoding
market-encoder-simple --config config/securities_simple.yaml

# Run full encoding with technical indicators
market-encoder-daily --config config/securities.yaml

# Test locally
market-encoder-test
```

### Development

```bash
# Format code
black src/ scripts/

# Lint code
ruff check src/ scripts/

# Run tests
pytest tests/
```

## 📦 Package Structure

### Market Encoder (`src/market_encoder/`)

- **`core/`**: Main encoding logic and orchestration
- **`data/`**: Data source integrations (Yahoo Finance, Alpha Vantage)
- **`signals/`**: Technical indicator calculations and signal generation
- **`storage/`**: Database storage backends (PostgreSQL, ChromaDB)
- **`config/`**: Configuration loading and validation

### Scripts (`scripts/`)

Entry point scripts that can be run directly or via `pyproject.toml` console scripts:

- `market-encoder-daily`: Full market encoder with technical indicators
- `market-encoder-simple`: Simple daily price encoder (no indicators)
- `market-encoder-test`: Local testing and validation

## 🔧 Configuration

Securities and encoding settings are configured via YAML files in `config/`:

```yaml
securities:
  indices:
    - symbol: "^GSPC"
      name: "S&P 500 Index"
      enabled: true
  # ... more securities

encoding:
  days_back: 60
  batch_size: 10
  # ... more settings
```

## 🚀 Deployment

### Local Development
```bash
python scripts/simple_daily_encoding.py --config config/securities_simple.yaml
```

### Kubernetes
```bash
# Deploy namespace and shared resources
kubectl apply -f deploy/k8s/shared/

# Deploy market encoder
kubectl apply -f deploy/k8s/market-encoder/

# Create manual job
kubectl create job --from=cronjob/simple-market-encoder-daily test-run -n time-series-indexing
```

### Docker
```bash
# Build image
docker build -f deploy/docker/market-encoder.Dockerfile -t market-encoder .

# Run container
docker run -e DB_HOST=localhost market-encoder
```

## 🗄️ Database Schema

The system uses dual storage:

- **PostgreSQL**: Structured market data for queries and P&L calculations
- **ChromaDB**: Market narratives and embeddings for semantic search

See `sql/migrations/` for database schema definitions.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Test specific module
pytest tests/test_market_encoder.py
```

## 📈 Future Packages

- **`astro_encoder/`**: Astronomical data encoding (planned)
- **`shared/`**: Common utilities and base classes