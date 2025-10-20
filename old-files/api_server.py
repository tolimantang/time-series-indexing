#!/usr/bin/env python3
"""
API Server: Handles queries for astro-financial correlation system
Supports both semantic search (ChromaDB) and structured queries (PostgreSQL)
"""

import os
import sys
import psycopg2
import chromadb
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import json
import logging
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add project modules to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from astro_embedding_pipeline import AstroEmbeddingPipeline


# Pydantic models for API requests/responses
class SemanticQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query", example="moon opposite saturn")
    max_results: int = Field(10, ge=1, le=100, description="Maximum number of results")
    collection_name: str = Field("astronomical_detailed", description="ChromaDB collection to search")
    include_market_data: bool = Field(True, description="Include market data in results")


class StructuredQueryRequest(BaseModel):
    planet1: Optional[str] = Field(None, example="moon")
    planet2: Optional[str] = Field(None, example="saturn")
    aspect_type: Optional[str] = Field(None, example="opposition")
    max_orb: Optional[float] = Field(8.0, description="Maximum orb in degrees")
    jupiter_sign: Optional[str] = Field(None, example="cancer")
    date_start: Optional[str] = Field(None, example="2020-01-01")
    date_end: Optional[str] = Field(None, example="2024-12-31")
    max_results: int = Field(50, ge=1, le=1000)


class PatternAnalysisRequest(BaseModel):
    query: str = Field(..., description="Pattern to analyze")
    lookback_days: int = Field(30, ge=1, le=365, description="Days before/after to analyze")
    target_assets: List[str] = Field(["SPY", "VIX", "EURUSD"], description="Assets to analyze")


class QueryResponse(BaseModel):
    query_type: str
    results_count: int
    results: List[Dict[str, Any]]
    execution_time_ms: float
    metadata: Dict[str, Any]


class AstroFinancialAPI:
    """FastAPI server for astro-financial queries."""

    def __init__(self,
                 pg_connection_string: Optional[str] = None,
                 chroma_persist_directory: Optional[str] = None):

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Database connections
        self.pg_connection_string = (pg_connection_string or
                                   os.getenv('POSTGRES_CONNECTION_STRING',
                                            'postgresql://localhost:5432/astro_financial'))
        self.pg_conn = None

        # ChromaDB directory
        chroma_dir = chroma_persist_directory or './chroma_data'

        # Initialize embedding pipeline (it will create its own ChromaDB client)
        self.astro_pipeline = AstroEmbeddingPipeline(chroma_path=chroma_dir)

        # Get the ChromaDB client from the pipeline
        self.chroma_client = self.astro_pipeline.chroma_client

        self.logger.info("✓ API server initialized")

    def connect_postgres(self):
        """Connect to PostgreSQL."""
        if not self.pg_conn or self.pg_conn.closed:
            try:
                self.pg_conn = psycopg2.connect(self.pg_connection_string)
                self.logger.info("✓ Connected to PostgreSQL")
            except Exception as e:
                self.logger.error(f"Failed to connect to PostgreSQL: {e}")
                raise HTTPException(status_code=500, detail="Database connection failed")

    def semantic_search(self, request: SemanticQueryRequest) -> QueryResponse:
        """Perform semantic search using ChromaDB."""
        start_time = datetime.now()

        try:
            # Perform ChromaDB search
            search_results = self.astro_pipeline.search_similar_patterns(
                query=request.query,
                collection_name=request.collection_name,
                n_results=request.max_results
            )

            results = search_results['results']

            # Optionally include market data
            if request.include_market_data and results:
                results = self._enrich_with_market_data(results)

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return QueryResponse(
                query_type="semantic_search",
                results_count=len(results),
                results=results,
                execution_time_ms=execution_time,
                metadata={
                    "query": request.query,
                    "collection": request.collection_name,
                    "include_market_data": request.include_market_data
                }
            )

        except Exception as e:
            self.logger.error(f"Semantic search error: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    def structured_query(self, request: StructuredQueryRequest) -> QueryResponse:
        """Perform structured query using PostgreSQL."""
        start_time = datetime.now()
        self.connect_postgres()

        try:
            # Build SQL query
            where_conditions = []
            params = []

            # Date range filter
            if request.date_start:
                where_conditions.append("dr.date >= %s")
                params.append(request.date_start)
            if request.date_end:
                where_conditions.append("dr.date <= %s")
                params.append(request.date_end)

            # Jupiter sign filter
            if request.jupiter_sign:
                where_conditions.append("ad.jupiter_sign = %s")
                params.append(request.jupiter_sign)

            # Aspect filter (using JSON queries)
            if request.planet1 and request.planet2 and request.aspect_type:
                aspect_condition = """
                    ad.all_aspects @> %s::jsonb
                """
                aspect_filter = [{
                    "planet1": request.planet1,
                    "planet2": request.planet2,
                    "aspect_type": request.aspect_type
                }]
                where_conditions.append(aspect_condition)
                params.append(json.dumps(aspect_filter))

            # Build WHERE clause
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Execute query
            cursor = self.pg_conn.cursor()
            query = f"""
                SELECT
                    dr.date,
                    dr.data_quality_score,
                    ad.jupiter_sign,
                    ad.moon_sign,
                    ad.lunar_phase,
                    ad.major_conjunctions,
                    fnd.market_regime,
                    fnd.daily_summary
                FROM daily_records dr
                LEFT JOIN astronomical_data ad ON dr.date = ad.date
                LEFT JOIN financial_news_data fnd ON dr.date = fnd.date
                WHERE {where_clause}
                ORDER BY dr.date DESC
                LIMIT %s
            """
            params.append(request.max_results)

            cursor.execute(query, params)
            raw_results = cursor.fetchall()

            # Format results
            results = []
            for row in raw_results:
                results.append({
                    'date': str(row[0]) if row[0] else None,
                    'data_quality_score': float(row[1]) if row[1] else None,
                    'jupiter_sign': row[2],
                    'moon_sign': row[3],
                    'lunar_phase': float(row[4]) if row[4] else None,
                    'major_conjunctions': row[5],
                    'market_regime': row[6],
                    'daily_summary': row[7]
                })

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return QueryResponse(
                query_type="structured_query",
                results_count=len(results),
                results=results,
                execution_time_ms=execution_time,
                metadata={
                    "filters": {
                        "planet1": request.planet1,
                        "planet2": request.planet2,
                        "aspect_type": request.aspect_type,
                        "jupiter_sign": request.jupiter_sign,
                        "date_range": f"{request.date_start} to {request.date_end}"
                    }
                }
            )

        except Exception as e:
            self.logger.error(f"Structured query error: {e}")
            raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    def pattern_analysis(self, request: PatternAnalysisRequest) -> QueryResponse:
        """Analyze market effects of astronomical patterns."""
        start_time = datetime.now()

        try:
            # First, find matching astronomical patterns
            semantic_results = self.astro_pipeline.search_similar_patterns(
                query=request.query,
                n_results=50  # Get more results for statistical analysis
            )

            matching_dates = [r['date'] for r in semantic_results['results']]

            if not matching_dates:
                return QueryResponse(
                    query_type="pattern_analysis",
                    results_count=0,
                    results=[],
                    execution_time_ms=0,
                    metadata={"message": "No matching patterns found"}
                )

            # Analyze market effects (simulated - would query real market data)
            analysis_results = self._analyze_market_effects(
                matching_dates,
                request.lookback_days,
                request.target_assets
            )

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return QueryResponse(
                query_type="pattern_analysis",
                results_count=len(analysis_results),
                results=analysis_results,
                execution_time_ms=execution_time,
                metadata={
                    "query": request.query,
                    "matching_periods": len(matching_dates),
                    "lookback_days": request.lookback_days,
                    "target_assets": request.target_assets
                }
            )

        except Exception as e:
            self.logger.error(f"Pattern analysis error: {e}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    def _enrich_with_market_data(self, results: List[Dict]) -> List[Dict]:
        """Add market data to search results (simulated)."""
        self.connect_postgres()
        cursor = self.pg_conn.cursor()

        enriched_results = []
        for result in results:
            date = result.get('date')
            if not date:
                enriched_results.append(result)
                continue

            try:
                # Query financial data for this date
                cursor.execute("""
                    SELECT market_regime, daily_summary, combined_summary
                    FROM financial_news_data
                    WHERE date = %s
                """, (date,))

                financial_data = cursor.fetchone()
                if financial_data:
                    result['market_regime'] = financial_data[0]
                    result['daily_summary'] = financial_data[1]
                    result['combined_summary'] = financial_data[2]

                enriched_results.append(result)

            except Exception as e:
                self.logger.warning(f"Could not enrich market data for {date}: {e}")
                enriched_results.append(result)

        return enriched_results

    def _analyze_market_effects(self, dates: List[str], lookback_days: int,
                              target_assets: List[str]) -> List[Dict]:
        """Analyze market effects for given dates (simulated analysis)."""
        # In production, this would query real market data
        # For now, return simulated statistical analysis

        import random
        random.seed(42)  # For reproducible results

        analysis_results = []

        for asset in target_assets:
            # Simulate market analysis
            returns = [random.gauss(-0.1, 2.0) for _ in dates]  # Simulated returns
            volatilities = [abs(random.gauss(15, 5)) for _ in dates]  # Simulated volatilities

            analysis_results.append({
                'asset': asset,
                'sample_size': len(dates),
                'avg_return': sum(returns) / len(returns) if returns else 0,
                'volatility': sum(volatilities) / len(volatilities) if volatilities else 0,
                'return_distribution': {
                    'positive_days': len([r for r in returns if r > 0]),
                    'negative_days': len([r for r in returns if r < 0]),
                    'neutral_days': len([r for r in returns if r == 0])
                },
                'significant_moves': [
                    {'date': dates[i], 'return': returns[i]}
                    for i, ret in enumerate(returns)
                    if abs(ret) > 2.0
                ]
            })

        return analysis_results

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
            self.connect_postgres()
            cursor = self.pg_conn.cursor()

            # Get PostgreSQL stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(DISTINCT date) as unique_dates,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date,
                    AVG(data_quality_score) as avg_quality
                FROM daily_records
            """)

            pg_stats = cursor.fetchone()

            # Get ChromaDB stats
            try:
                chroma_stats = {
                    'astro_detailed': self.astro_pipeline.astro_detailed.count(),
                    'astro_patterns': self.astro_pipeline.astro_patterns.count()
                }
            except:
                chroma_stats = {'error': 'Could not retrieve ChromaDB stats'}

            return {
                'status': 'healthy',
                'postgresql': {
                    'total_records': pg_stats[0] if pg_stats else 0,
                    'unique_dates': pg_stats[1] if pg_stats else 0,
                    'date_range': {
                        'start': str(pg_stats[2]) if pg_stats and pg_stats[2] else None,
                        'end': str(pg_stats[3]) if pg_stats and pg_stats[3] else None
                    },
                    'avg_quality_score': float(pg_stats[4]) if pg_stats and pg_stats[4] else 0
                },
                'chromadb': chroma_stats,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }


# Initialize FastAPI app
app = FastAPI(
    title="Astro-Financial API",
    description="API for querying astronomical-financial correlations",
    version="1.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize API instance
api_instance = AstroFinancialAPI()


# API Routes
@app.get("/")
async def root():
    """API root endpoint."""
    return {"message": "Astro-Financial API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return api_instance.get_system_stats()


@app.post("/query/semantic", response_model=QueryResponse)
async def semantic_search(request: SemanticQueryRequest):
    """Perform semantic search using natural language queries."""
    return api_instance.semantic_search(request)


@app.post("/query/structured", response_model=QueryResponse)
async def structured_query(request: StructuredQueryRequest):
    """Perform structured queries using specific parameters."""
    return api_instance.structured_query(request)


@app.post("/analysis/pattern", response_model=QueryResponse)
async def pattern_analysis(request: PatternAnalysisRequest):
    """Analyze market effects of astronomical patterns."""
    return api_instance.pattern_analysis(request)


@app.get("/query/examples")
async def get_query_examples():
    """Get example queries for frontend."""
    return {
        "semantic_queries": [
            "moon opposite saturn",
            "jupiter in cancer",
            "mercury mars conjunction",
            "saturn neptune conjunction",
            "multiple tight aspects",
            "venus retrograde"
        ],
        "structured_query_examples": [
            {
                "description": "Moon-Saturn oppositions in 2024",
                "params": {
                    "planet1": "moon",
                    "planet2": "saturn",
                    "aspect_type": "opposition",
                    "date_start": "2024-01-01",
                    "date_end": "2024-12-31"
                }
            },
            {
                "description": "Jupiter in Cancer periods",
                "params": {
                    "jupiter_sign": "cancer",
                    "date_start": "2020-01-01",
                    "date_end": "2024-12-31"
                }
            }
        ],
        "pattern_analysis_examples": [
            {
                "query": "saturn neptune conjunction",
                "lookback_days": 30,
                "target_assets": ["SPY", "VIX", "EURUSD"]
            }
        ]
    }


# Run server
def run_server(host: str = "0.0.0.0", port: int = 8000, debug: bool = True):
    """Run the FastAPI server."""
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )


if __name__ == "__main__":
    print("Starting Astro-Financial API Server...")
    run_server()