# Financial MCP Tools

This directory contains MCP (Model Context Protocol) tools for financial data analysis.

## Fed Rate Changes Tool

The `FedRateChangesTool` allows natural language queries about Federal Reserve rate changes using LLM-generated WHERE clauses.

### Features

- **Natural Language Queries**: Ask questions like "Fed increases rates by more than 0.25% after 2020"
- **LLM-Powered SQL Generation**: Uses Claude Haiku to convert natural language to SQL WHERE clauses
- **Security**: Only generates WHERE clauses, never full SQL queries
- **Fallback Support**: Falls back to keyword-based parsing if LLM is unavailable
- **Market Impact Analysis**: Optional analysis of how rate changes affect specific assets

### Usage

#### Via API Server

```bash
# Test the tool via the query service
curl -X POST http://localhost:8003/tools/fed_rate_changes \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Fed increases rates by more than 0.25% after 2020",
    "target_asset": "GLD",
    "impact_days": 30
  }'
```

#### Direct Usage

```python
from src.mcp_tools.financial.fed_rate_tools import FedRateChangesTool

# Initialize with dependencies
tool = FedRateChangesTool(
    postgres_manager=postgres_manager,
    market_data_manager=market_data_manager,
    anthropic_api_key="your-api-key"  # Optional, uses ANTHROPIC_API_KEY env var
)

# Execute natural language query
result = tool.execute(
    query="Fed cuts rates during financial crisis",
    target_asset="SPY",
    impact_days=30
)
```

### Example Queries

- "Fed increases rates by more than 0.25% after 2020"
- "Large Fed rate cuts during 2008 financial crisis"
- "All Fed decisions in recent years"
- "Emergency rate cuts greater than 0.5%"
- "Fed raises rates while unemployment is high"

### Response Format

```json
{
  "success": true,
  "data": {
    "query_parameters": {
      "original_query": "Fed increases rates after 2020",
      "generated_where_clause": "event_type = %s AND change_amount > %s AND event_date > %s",
      "target_asset": "GLD"
    },
    "fed_rate_events": [
      {
        "event_id": 1,
        "event_date": "2022-03-16",
        "title": "Fed Raises Rates",
        "change_amount": 0.25,
        "importance": 5
      }
    ],
    "total_events": 1,
    "summary_statistics": {
      "average_magnitude": 0.375,
      "largest_change": 0.5,
      "smallest_change": 0.25
    },
    "market_impact_analysis": {
      "target_asset": "GLD",
      "aggregate_statistics": {
        "average_5d_return": -1.2,
        "success_rate": 33.3
      }
    }
  }
}
```

### Environment Variables

- `ANTHROPIC_API_KEY`: Required for LLM-powered WHERE clause generation
- Database connection variables (inherited from postgres_manager)

### Architecture

1. **Input**: Natural language query about Fed rate changes
2. **LLM Processing**: Claude Haiku converts query to SQL WHERE clause
3. **Validation**: Generated clauses are validated against allowed columns
4. **Execution**: Combined with base query structure for safe execution
5. **Market Analysis**: Optional impact analysis on target assets
6. **Response**: Structured results with transparency about generated SQL

### Security Features

- Parameterized queries prevent SQL injection
- Only WHERE clauses generated, never full queries
- Column/table allowlisting in LLM prompt
- Graceful fallback to keyword parsing
- No direct user input in SQL execution

### Deployment

The tool is automatically deployed via GitHub Actions when changes are pushed to main:

1. Docker image built and pushed to ECR
2. Kubernetes secrets updated (including Anthropic API key)
3. Query service deployed with new tool
4. Basic functionality tests executed

See `.github/workflows/deploy-query-service.yml` for full deployment pipeline.