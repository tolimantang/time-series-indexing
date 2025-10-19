# Market Encoder E2E Setup

Complete end-to-end setup for the daily market encoder cronjob that fetches configurable securities and stores data in both PostgreSQL and ChromaDB.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Yahoo Finance  │───▶│ Market Encoder  │───▶│   PostgreSQL    │
│   (Data Source) │    │   (Processing)  │    │ (Time-series)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │    ChromaDB     │
                       │  (Embeddings)   │
                       └─────────────────┘
```

## 📁 Project Structure

```
backend/
├── market_encoder/
│   ├── config.py           # Configuration loader
│   ├── multi_encoder.py    # Multi-security processor
│   ├── encoder.py          # Base encoder (updated)
│   └── ...
├── config/
│   └── securities.yaml     # Securities configuration
├── scripts/
│   ├── daily_market_encoding.py  # Main cronjob script
│   └── test_market_encoder.py    # Local testing
├── k8s/
│   ├── market-encoder-cronjob.yaml    # Kubernetes cronjob
│   └── market-encoder-config.yaml     # ConfigMap & Secret
├── sql/
│   ├── migrations/
│   │   └── 002_add_market_data.sql    # Market data schema
│   └── scripts/
│       └── run_migration.py           # Migration runner
└── docker-compose.test.yml  # Local testing environment
```

## 🚀 Quick Start

### 1. Local Testing

```bash
# 1. Start test environment
cd backend
docker-compose -f docker-compose.test.yml up -d postgres-test

# 2. Run database migrations
python sql/scripts/run_migration.py run

# 3. Test configuration and single security
python scripts/test_market_encoder.py

# 4. Test full daily encoding (indices only)
docker-compose -f docker-compose.test.yml up market-encoder-daily-test
```

### 2. Configure Securities

Edit `config/securities.yaml`:

```yaml
securities:
  indices:
    - symbol: "^GSPC"
      name: "S&P 500 Index"
      yahoo_symbol: "^GSPC"
      db_symbol: "SPX"
      enabled: true  # Set to false to disable
```

### 3. Deploy to Kubernetes

```bash
# 1. Update database secrets in k8s/market-encoder-config.yaml
# 2. Build and push Docker image
docker build -f Dockerfile.market-encoder -t your-registry/market-encoder:latest .
docker push your-registry/market-encoder:latest

# 3. Deploy to Kubernetes
kubectl apply -f k8s/market-encoder-config.yaml
kubectl apply -f k8s/market-encoder-cronjob.yaml

# 4. Test manually
kubectl create job --from=cronjob/market-encoder-daily test-run -n time-series-indexing
```

## ⚙️ Configuration

### Securities Configuration (`config/securities.yaml`)

```yaml
securities:
  indices:     # Market indices
  etfs:        # Exchange-traded funds
  stocks:      # Individual stocks
  crypto:      # Cryptocurrencies

encoding:
  days_back: 60              # Days of data to fetch
  embedding_days: 30         # Days to process for embeddings
  batch_size: 5              # Securities per batch
  max_retries: 3             # Retry attempts
```

### Environment Variables

**Required:**
- `DB_HOST` - PostgreSQL hostname
- `DB_NAME` - Database name
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password

**Optional:**
- `DB_PORT` - Database port (default: 5432)
- `CHROMA_DB_PATH` - ChromaDB storage path
- `LOG_LEVEL` - Logging level (default: INFO)

## 🗄️ Database Schema

### Market Data Table (PostgreSQL)

```sql
CREATE TABLE market_data (
    id UUID PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(12,4),
    high_price DECIMAL(12,4),
    low_price DECIMAL(12,4),
    close_price DECIMAL(12,4),
    volume BIGINT,
    daily_return DECIMAL(8,6),
    UNIQUE(symbol, trade_date)
);
```

### ChromaDB Collections

- **Collection**: `sp500_market_data`
- **Documents**: Market narratives and analysis
- **Metadata**: Price, volatility, technical indicators, regime data

## 📊 P&L Calculations

Calculate hypothetical profit/loss between dates:

```python
from market_encoder.multi_encoder import MultiSecurityEncoder

encoder = MultiSecurityEncoder()
pnl = encoder.encoder.calculate_hypothetical_pnl(
    symbol='SPX',
    entry_date='2024-01-01',
    exit_date='2024-01-31',
    quantity=100,
    position_type='long'
)

print(f"P&L: ${pnl['pnl_amount']} ({pnl['pnl_percentage']:.2f}%)")
```

## ⏰ Cronjob Schedule

**Default Schedule**: `30 6 * * 1-5` (6:30 AM UTC, weekdays only)

This runs after US markets close (4:00 PM EST = 9:00 PM UTC).

### Customizing Schedule

Edit `schedule` in `k8s/market-encoder-cronjob.yaml`:

```yaml
spec:
  schedule: "30 6 * * 1-5"  # 6:30 AM UTC weekdays
  # schedule: "0 22 * * 1-5"  # 10:00 PM UTC weekdays
  # schedule: "0 */6 * * *"   # Every 6 hours
```

## 🧪 Testing Commands

```bash
# Test configuration only
python scripts/daily_market_encoding.py --dry-run

# Test specific categories
python scripts/daily_market_encoding.py --categories indices etfs

# Test with verbose logging
python scripts/daily_market_encoding.py --verbose

# Test in Docker
docker-compose -f docker-compose.test.yml up market-encoder-test

# Test Kubernetes job manually
kubectl create job --from=cronjob/market-encoder-daily manual-test -n time-series-indexing
kubectl logs job/manual-test -n time-series-indexing -f
```

## 📈 Monitoring

### Check Cronjob Status

```bash
# List cronjobs
kubectl get cronjobs -n time-series-indexing

# Check recent jobs
kubectl get jobs -n time-series-indexing --sort-by=.metadata.creationTimestamp

# View logs
kubectl logs -l app=market-encoder -n time-series-indexing --tail=100
```

### View Results

```bash
# Check PostgreSQL data
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT symbol, COUNT(*), MIN(trade_date), MAX(trade_date)
FROM market_data
GROUP BY symbol ORDER BY symbol;
"

# Check ChromaDB collection
python -c "
import chromadb
client = chromadb.PersistentClient(path='/data/chroma_market_db')
collection = client.get_collection('sp500_market_data')
print(f'ChromaDB records: {collection.count()}')
"
```

## 🔧 Troubleshooting

### Common Issues

1. **No data retrieved**: Check Yahoo Finance symbol format
2. **Database connection failed**: Verify credentials and network access
3. **ChromaDB permission errors**: Check volume mounts and file permissions
4. **Out of memory**: Increase resource limits or reduce batch size

### Debug Commands

```bash
# Check pod status
kubectl describe pod -l app=market-encoder -n time-series-indexing

# View detailed logs
kubectl logs -l app=market-encoder -n time-series-indexing --previous

# Exec into pod for debugging
kubectl exec -it deployment/market-encoder -n time-series-indexing -- bash

# Test database connection
kubectl exec -it deployment/market-encoder -n time-series-indexing -- python -c "
import psycopg2
conn = psycopg2.connect(host='$DB_HOST', database='$DB_NAME', user='$DB_USER', password='$DB_PASSWORD')
print('Database connection successful')
"
```

## 🔐 Security Notes

- Database credentials are stored in Kubernetes secrets
- Container runs as non-root user
- Network policies should restrict database access
- Consider using AWS RDS IAM authentication for production

## 📋 Production Checklist

- [ ] Update database credentials in `k8s/market-encoder-config.yaml`
- [ ] Configure appropriate resource limits
- [ ] Set up database backups
- [ ] Configure monitoring and alerting
- [ ] Test P&L calculations with real data
- [ ] Verify cronjob schedule matches market hours
- [ ] Set up log aggregation
- [ ] Configure persistent volume for ChromaDB