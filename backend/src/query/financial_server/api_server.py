"""
Financial Query API Server

FastAPI server that provides intelligent querying capabilities for financial data.
Handles complex questions like "What happens to platinum prices after Fed raises interest rates?"
"""

import logging
from datetime import date, datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

try:
    from .query_engine import FinancialQueryEngine
except ImportError:
    # Handle direct script execution
    from query_engine import FinancialQueryEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Financial Query API",
    description="Intelligent financial event analysis and querying system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize query engine
query_engine = FinancialQueryEngine()


# Request/Response Models

class CausalAnalysisRequest(BaseModel):
    # Support both structured and natural language queries
    trigger_event_type: Optional[str] = Field(None, description="Type of triggering event (e.g., 'fed_decision') - optional if trigger_query provided")
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict, description="Conditions for the trigger")
    trigger_query: Optional[str] = Field(None, description="Natural language description of trigger events (e.g., 'Fed raises interest rates')")
    impact_timeframe_days: int = Field(30, description="Days to look ahead for impacts")
    limit: int = Field(3, description="Maximum number of trigger events to analyze")
    target_asset: Optional[str] = Field(None, description="Optional asset symbol for price impact analysis (e.g., 'GLD', 'SPY')")
    time_range: Optional[Dict[str, str]] = Field(None, description="Optional specific time range for analysis (start_date, end_date)")

    class Config:
        schema_extra = {
            "examples": [
                {
                    "title": "Structured Query",
                    "value": {
                        "trigger_event_type": "fed_decision",
                        "trigger_conditions": {"change_direction": "increase"},
                        "target_asset": "GLD"
                    }
                },
                {
                    "title": "Natural Language Query",
                    "value": {
                        "trigger_query": "Fed raises interest rates",
                        "target_asset": "GLD",
                        "impact_timeframe_days": 30
                    }
                }
            ]
        }


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    start_date: Optional[str] = Field(None, description="Start date filter (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date filter (YYYY-MM-DD)")
    event_types: Optional[List[str]] = Field(None, description="Event type filter")
    n_results: int = Field(10, description="Number of results to return")

    class Config:
        schema_extra = {
            "example": {
                "query": "Federal Reserve interest rate decisions affecting markets",
                "start_date": "2020-01-01",
                "end_date": "2024-12-31",
                "n_results": 15
            }
        }


class TimeSeriesAnalysisRequest(BaseModel):
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    event_types: Optional[List[str]] = Field(None, description="Event type filter")
    importance: Optional[List[str]] = Field(None, description="Importance filter (high, medium, low)")

    class Config:
        schema_extra = {
            "example": {
                "start_date": "2020-01-01",
                "end_date": "2024-12-31",
                "event_types": ["fed_decision", "employment_data"],
                "importance": ["high"]
            }
        }


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Financial Query API",
        "version": "1.0.0",
        "description": "Intelligent financial event analysis and querying",
        "capabilities": [
            "Causal impact analysis",
            "Semantic search",
            "Time series analysis",
            "Cross-market correlation"
        ],
        "example_queries": [
            "What happens after Fed rate increases?",
            "How do unemployment changes affect markets?",
            "Find inflation-related events in 2022"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test both storage connections
        pg_stats = query_engine.postgres_manager.get_event_statistics()
        chroma_stats = query_engine.chroma_manager.get_collection_stats("financial_events")

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "storage": {
                "postgresql": {
                    "status": "connected",
                    "total_events": pg_stats.get("total_events", 0)
                },
                "chromadb": {
                    "status": "connected",
                    "total_documents": chroma_stats.get("total_documents", 0)
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/query/causal-analysis")
async def causal_analysis(request: CausalAnalysisRequest):
    """
    Analyze causal relationships between events.

    Example: What happens after Fed rate increases?
    """
    try:
        result = query_engine.analyze_causal_impact(
            trigger_event_type=request.trigger_event_type,
            trigger_conditions=request.trigger_conditions,
            trigger_query=request.trigger_query,
            impact_timeframe_days=request.impact_timeframe_days,
            limit=request.limit,
            target_asset=request.target_asset,
            time_range=request.time_range
        )

        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])

        return result

    except Exception as e:
        logger.error(f"Causal analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/semantic-search")
async def semantic_search(request: SemanticSearchRequest):
    """
    Perform semantic search across financial events.

    Uses natural language processing to find relevant events.
    """
    try:
        # Parse date range if provided
        date_range = None
        if request.start_date and request.end_date:
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date()
            date_range = (start_date, end_date)

        result = query_engine.semantic_search(
            query=request.query,
            date_range=date_range,
            event_types=request.event_types,
            n_results=request.n_results
        )

        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/time-series")
async def time_series_analysis(request: TimeSeriesAnalysisRequest):
    """
    Analyze events over a time period with statistics and patterns.
    """
    try:
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date()

        result = query_engine.time_series_analysis(
            start_date=start_date,
            end_date=end_date,
            event_types=request.event_types,
            importance=request.importance
        )

        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Time series analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/query/simple")
async def simple_query(
    q: str = Query(..., description="Natural language query"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(10, description="Maximum results")
):
    """
    Simple query endpoint for quick natural language questions.

    Examples:
    - /query/simple?q=What happens after Fed rate increases?
    - /query/simple?q=unemployment changes in 2020&start_date=2020-01-01&end_date=2020-12-31
    """
    try:
        # Determine query type based on content
        q_lower = q.lower()

        if any(phrase in q_lower for phrase in ['what happens after', 'impact of', 'effect of', 'following']):
            # Causal analysis query
            if 'fed' in q_lower and any(word in q_lower for word in ['raise', 'increase', 'cut', 'decrease']):
                trigger_conditions = {}
                if any(word in q_lower for word in ['raise', 'increase']):
                    trigger_conditions['change_direction'] = 'increase'
                elif any(word in q_lower for word in ['cut', 'decrease']):
                    trigger_conditions['change_direction'] = 'decrease'

                result = query_engine.analyze_causal_impact(
                    trigger_event_type='fed_decision',
                    trigger_conditions=trigger_conditions,
                    impact_timeframe_days=30,
                    limit=limit
                )
            else:
                # Generic semantic search
                date_range = None
                if start_date and end_date:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                    date_range = (start_dt, end_dt)

                result = query_engine.semantic_search(
                    query=q,
                    date_range=date_range,
                    n_results=limit
                )
        else:
            # Regular semantic search
            date_range = None
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                date_range = (start_dt, end_dt)

            result = query_engine.semantic_search(
                query=q,
                date_range=date_range,
                n_results=limit
            )

        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])

        return {
            "query": q,
            "query_type": "inferred",
            "result": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.error(f"Simple query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# MCP Tool endpoints

@app.get("/tools")
async def list_mcp_tools():
    """List all available MCP tools and their schemas."""
    try:
        tools = query_engine.get_available_mcp_tools()
        return {
            "available_tools": tools,
            "tool_count": len(tools),
            "usage": "Use POST /tools/{tool_name} to execute a tool"
        }
    except Exception as e:
        logger.error(f"Error listing MCP tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/{tool_name}")
async def execute_mcp_tool(tool_name: str, parameters: Dict[str, Any]):
    """
    Execute an MCP tool with the provided parameters.

    This endpoint allows the LLM to call specific tools for precise queries.
    """
    try:
        logger.info(f"MCP tool request: {tool_name} with parameters: {parameters}")

        result = query_engine.execute_mcp_tool(tool_name, **parameters)

        if not result.get('success', False):
            raise HTTPException(status_code=400, detail=result.get('error', 'Tool execution failed'))

        return result

    except Exception as e:
        logger.error(f"Error executing MCP tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Development endpoints

@app.get("/data/statistics")
async def get_data_statistics():
    """Get statistics about available data."""
    try:
        pg_stats = query_engine.postgres_manager.get_event_statistics()
        chroma_stats = query_engine.chroma_manager.get_collection_stats("financial_events")

        return {
            "postgresql_stats": pg_stats,
            "chromadb_stats": chroma_stats,
            "data_health": "Both systems operational"
        }
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/sample-events")
async def get_sample_events(limit: int = Query(5, description="Number of sample events")):
    """Get sample events to understand data structure."""
    try:
        events = query_engine.postgres_manager.get_events_by_date_range(
            date(2020, 1, 1), date.today()
        )

        # Return most recent events
        sample_events = sorted(events, key=lambda x: x['event_date'], reverse=True)[:limit]

        return {
            "sample_events": sample_events,
            "total_available": len(events),
            "note": "These are sample events from the database"
        }
    except Exception as e:
        logger.error(f"Sample events error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")