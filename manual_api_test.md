# Manual API Testing with Curl

Your API server is running at `http://localhost:8000`. Here are the exact curl commands:

## 1. Check if Server is Running

```bash
curl http://localhost:8000/
```

Expected response:
```json
{"message":"Astro-Financial API","version":"1.0.0","status":"running"}
```

## 2. Health Check

```bash
curl http://localhost:8000/health
```

## 3. Get Query Examples

```bash
curl http://localhost:8000/query/examples
```

## 4. Semantic Search (Main Feature)

```bash
curl -X POST http://localhost:8000/query/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "moon saturn aspects", "max_results": 3, "include_market_data": false}'
```

## 5. Different Search Queries

```bash
# Search for Jupiter patterns
curl -X POST http://localhost:8000/query/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "jupiter aspects", "max_results": 5}'

# Search for tight conjunctions
curl -X POST http://localhost:8000/query/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "tight planetary alignments", "max_results": 3}'

# Search for multiple aspects
curl -X POST http://localhost:8000/query/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "multiple conjunctions", "max_results": 3}'
```

## 6. Pattern Analysis

```bash
curl -X POST http://localhost:8000/analysis/pattern \
  -H "Content-Type: application/json" \
  -d '{"query": "saturn aspects", "lookback_days": 30, "target_assets": ["SPY", "VIX"]}'
```

## Tips:

1. **Pretty Print JSON**: Add `| python -m json.tool` to any curl command
   ```bash
   curl http://localhost:8000/ | python -m json.tool
   ```

2. **Check if server is running**:
   ```bash
   lsof -i :8000
   ```

3. **Stop the server**: Find the process and kill it
   ```bash
   ps aux | grep api_server
   kill [PID]
   ```

4. **Restart server**:
   ```bash
   python api_server.py
   ```

## Current Data in Your System:
- **10 astronomical dates** indexed (Sept-Oct 2025)
- **20 total embeddings** (detailed + patterns)
- **Sample queries working**: moon saturn aspects, jupiter aspects, tight alignments