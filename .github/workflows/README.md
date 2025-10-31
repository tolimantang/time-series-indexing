# GitHub Workflows

This directory contains GitHub Actions workflows for automated deployment and testing of the Time Series Indexing system.

## Workflow Overview

### 🏗️ Infrastructure
- **`deploy-infrastructure.yml`** - Deploys shared infrastructure (database migrations, secrets)
  - Triggers: SQL migration changes, manual dispatch
  - Creates: Kubernetes namespace, shared secrets, runs Flyway migrations

### 📊 Query Services
- **`deploy-query-service.yml`** - Deploys user-facing API services
  - **Query Service** (Port 8003): Natural language financial queries + Fed rate tool
  - **Recommendation Service** (Port 8002): Trading recommendations
  - Triggers: Changes to query/, mcp_tools/, recommendation service
  - Features: LLM-powered Fed rate tool with Anthropic API

### 🔄 Indexing Services
- **`deploy-indexing-services.yml`** - Deploys data processing services
  - **Backfill Service** (Port 8001): On-demand historical data backfill
  - **Backtesting Service** (Port 8000): Lunar pattern analysis and backtests
  - Triggers: Changes to backfill/backtesting services, llm_analyzer/

### 🧪 Testing
- **`test-fed-rate-tool.yml`** - Unit tests for Fed rate tool
  - Triggers: Pull requests affecting MCP tools or query services

## Legacy Files

- **`deploy.yml`** - Legacy monolithic deployment (now replaced by focused workflows above)

## Deployment Flow

1. **Infrastructure First**: Run `deploy-infrastructure.yml` to set up base resources
2. **Services Deploy Independently**:
   - Query services deploy when query/MCP code changes
   - Indexing services deploy when backfill/backtesting code changes
3. **Automatic Testing**: Each deployment includes health checks and functional tests

## Required Secrets

Configure these in GitHub repository secrets:

### AWS
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### Database
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

### External APIs
- `FRED_API_KEY` - Federal Reserve Economic Data API
- `CHROMA_API_KEY` - ChromaDB Cloud API
- `CHROMA_TENANT` - ChromaDB tenant
- `CHROMA_DATABASE` - ChromaDB database
- `ANTHROPIC_API_KEY` - Claude API for LLM-powered Fed rate tool

## Architecture Benefits

- **Fast Deployments**: Only changed services redeploy
- **Independent Teams**: Teams can deploy their services independently
- **Better Testing**: Focused tests per service
- **Clear Separation**: Infrastructure vs application deployments
- **Reduced Risk**: Smaller, focused deployments reduce blast radius

## Service Dependencies

```
┌─────────────────┐    ┌─────────────────┐
│ Query Service   │    │ Recommendation │
│ (Port 8003)     │    │ Service         │
│ + Fed Rate Tool │    │ (Port 8002)     │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
          ┌─────────────────┐
          │  Infrastructure │
          │  - Database     │
          │  - Secrets      │
          │  - ChromaDB     │
          └─────────────────┘
                     │
         ┌───────────┬───────────┐
         │                       │
┌─────────────────┐    ┌─────────────────┐
│ Backfill Service│    │ Backtesting     │
│ (Port 8001)     │    │ Service         │
│                 │    │ (Port 8000)     │
└─────────────────┘    └─────────────────┘
```

## Usage Examples

### Deploy Everything
```bash
# Trigger all workflows manually
gh workflow run deploy-infrastructure.yml
gh workflow run deploy-query-service.yml
gh workflow run deploy-indexing-services.yml
```

### Deploy Only Query Services (with Fed Rate Tool)
```bash
gh workflow run deploy-query-service.yml
```

### Force Database Migration
```bash
gh workflow run deploy-infrastructure.yml -f force_migrations=true
```