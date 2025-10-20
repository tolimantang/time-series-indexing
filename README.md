# Time Series Indexing

A full-stack system for indexing and analyzing financial time series data with semantic search capabilities.

## 🏗️ Project Structure

```
time-series-indexing/
├── backend/              # Python backend services
│   ├── src/              # Python packages
│   ├── deploy/           # Kubernetes & Docker configs
│   ├── scripts/          # CLI tools
│   ├── config/           # Configuration files
│   └── sql/              # Database migrations
├── frontend/             # React/TypeScript frontend
├── terraform/            # Infrastructure as code
├── docs/                 # Project documentation
├── old-files/            # Archived experimental code
├── docker-compose.yml    # Local development
└── pyproject.toml        # Root Python configuration
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- kubectl (for deployment)

### Local Development

```bash
# Backend
cd backend
pip install -e .
market-encoder-simple --config config/securities_simple.yaml

# Frontend
cd frontend
npm install
npm run dev

# Full stack with Docker
docker-compose up
```

## 📚 Documentation

See the [`docs/`](./docs/) directory for detailed documentation:

- **[Product Architecture](./docs/product_architecture.md)** - System overview
- **[Backend README](./backend/README.md)** - Backend service details
- **[Codebase Analysis](./docs/CODEBASE_ANALYSIS.md)** - Code structure analysis
- **[Data Sources](./docs/DATA_SOURCES.md)** - Data integration details

## 🏛️ Architecture

### Backend Services
- **Market Encoder**: Fetches and encodes financial market data
- **Astro Encoder**: Astronomical data correlation (planned)
- **API Server**: REST API for frontend integration
- **Indexer**: Vector database management

### Data Storage
- **PostgreSQL**: Structured financial data
- **ChromaDB**: Vector embeddings for semantic search
- **Time-series optimization**: Fast queries for P&L calculations

### Frontend
- **React/TypeScript**: Modern web interface
- **Semantic Search**: Natural language market queries
- **Real-time Updates**: Live market data integration

## 🚀 Deployment

### Local Development
```bash
docker-compose up
```

### Kubernetes (EKS)
```bash
# Deploy infrastructure
kubectl apply -f backend/deploy/k8s/shared/

# Deploy services
kubectl apply -f backend/deploy/k8s/market-encoder/
```

### Infrastructure
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# End-to-end
npm run test:e2e
```

## 📊 Features

- **📈 Market Data Encoding**: Real-time financial data processing
- **🔍 Semantic Search**: Natural language queries for market analysis
- **📊 P&L Calculations**: Hypothetical profit/loss analysis
- **⚡ Fast Queries**: Optimized time-series data retrieval
- **🤖 Technical Indicators**: RSI, moving averages, Bollinger Bands
- **🌟 Market Narratives**: AI-generated market condition descriptions

## 🛠️ Development

### Adding New Features
1. Backend changes go in `backend/src/`
2. Frontend changes go in `frontend/src/`
3. Database changes go in `backend/sql/migrations/`
4. Infrastructure changes go in `terraform/`

### Code Organization
- **Monorepo**: All services in one repository
- **Clean Architecture**: Separated concerns and dependencies
- **Modern Tooling**: pyproject.toml, TypeScript, pytest
- **Docker**: Containerized development and deployment

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

For detailed setup instructions, see the respective README files in `backend/` and `frontend/` directories.