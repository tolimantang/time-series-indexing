#!/usr/bin/env python3
"""
Long-running Backtesting Service

A FastAPI service that accepts backtesting requests and runs lunar pattern analysis.
Much more efficient than one-off Kubernetes jobs.

Usage:
    POST /backtest
    {
        "symbol": "PLATINUM_FUTURES",
        "market_name": "PLATINUM",
        "timing_type": "next_day",
        "start_date": "2020-01-01",
        "end_date": "2024-10-01"
    }
"""

import os
import sys
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

# Add the analyzer to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'llm_analyzer'))
from enhanced_daily_lunar_tester import EnhancedDailyLunarTester

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Backtesting Service",
    description="Long-running service for lunar pattern backtesting",
    version="1.0.0"
)

# Pydantic models for request/response
class BacktestRequest(BaseModel):
    symbol: str = Field(..., description="Market symbol (e.g., PLATINUM_FUTURES)")
    market_name: str = Field(..., description="Market name (e.g., PLATINUM)")
    timing_type: str = Field(default="next_day", description="Timing type: same_day or next_day")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    accuracy_threshold: Optional[float] = Field(0.65, description="Minimum accuracy threshold")
    min_occurrences: Optional[int] = Field(5, description="Minimum pattern occurrences")

class BacktestResponse(BaseModel):
    request_id: str
    status: str
    message: str
    patterns_found: Optional[int] = None
    best_pattern: Optional[Dict[str, Any]] = None
    execution_time_seconds: Optional[float] = None

class PatternSummary(BaseModel):
    symbol: str
    market_name: str
    timing_type: str
    total_patterns: int
    best_accuracy: float
    best_pattern_name: str
    analysis_date: str

# In-memory storage for request tracking (in production, use Redis/DB)
active_requests: Dict[str, Dict] = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Backtesting Service",
        "status": "running",
        "version": "1.0.0",
        "active_requests": len(active_requests)
    }

@app.get("/health")
async def health_check():
    """Kubernetes health check"""
    try:
        # Test database connection
        tester = EnhancedDailyLunarTester()
        # Simple connection test
        tester.conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")

@app.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """Run backtesting analysis"""

    # Validate timing_type
    if request.timing_type not in ['same_day', 'next_day']:
        raise HTTPException(
            status_code=400,
            detail="timing_type must be 'same_day' or 'next_day'"
        )

    # Generate request ID
    request_id = f"{request.symbol}_{request.timing_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Track request
    active_requests[request_id] = {
        "status": "starting",
        "request": request.dict(),
        "start_time": datetime.now()
    }

    # Run backtest in background
    background_tasks.add_task(
        execute_backtest,
        request_id,
        request
    )

    return BacktestResponse(
        request_id=request_id,
        status="accepted",
        message=f"Backtesting started for {request.market_name} ({request.timing_type})"
    )

@app.get("/backtest/{request_id}", response_model=BacktestResponse)
async def get_backtest_status(request_id: str):
    """Get status of a backtesting request"""

    if request_id not in active_requests:
        raise HTTPException(status_code=404, detail="Request not found")

    request_info = active_requests[request_id]

    response = BacktestResponse(
        request_id=request_id,
        status=request_info["status"],
        message=request_info.get("message", ""),
        patterns_found=request_info.get("patterns_found"),
        best_pattern=request_info.get("best_pattern"),
        execution_time_seconds=request_info.get("execution_time")
    )

    return response

@app.get("/requests")
async def list_active_requests():
    """List all active/recent requests"""
    return {
        "active_requests": len(active_requests),
        "requests": [
            {
                "request_id": req_id,
                "status": info["status"],
                "symbol": info["request"]["symbol"],
                "timing_type": info["request"]["timing_type"],
                "start_time": info["start_time"].isoformat()
            }
            for req_id, info in active_requests.items()
        ]
    }

@app.get("/patterns/summary")
async def get_patterns_summary():
    """Get summary of all stored patterns"""
    try:
        tester = EnhancedDailyLunarTester()

        # Query pattern summary from database
        cursor = tester.conn.cursor()
        cursor.execute("""
            SELECT
                market_symbol,
                timing_type,
                COUNT(*) as total_patterns,
                MAX(accuracy_rate) as best_accuracy,
                (SELECT pattern_name FROM lunar_patterns lp2
                 WHERE lp2.market_symbol = lp.market_symbol
                 AND lp2.timing_type = lp.timing_type
                 ORDER BY accuracy_rate DESC LIMIT 1) as best_pattern_name
            FROM lunar_patterns lp
            GROUP BY market_symbol, timing_type
            ORDER BY market_symbol, timing_type
        """)

        results = cursor.fetchall()
        cursor.close()
        tester.conn.close()

        summaries = []
        for market_symbol, timing_type, total_patterns, best_accuracy, best_pattern_name in results:
            summaries.append(PatternSummary(
                symbol=market_symbol,
                market_name=market_symbol.replace('_DAILY', '').replace('_FUTURES', ''),
                timing_type=timing_type,
                total_patterns=total_patterns,
                best_accuracy=float(best_accuracy) if best_accuracy else 0.0,
                best_pattern_name=best_pattern_name or "None",
                analysis_date=datetime.now().date().isoformat()
            ))

        return {"summaries": summaries}

    except Exception as e:
        logger.error(f"Failed to get pattern summary: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

async def execute_backtest(request_id: str, request: BacktestRequest):
    """Execute the actual backtesting (runs in background)"""
    try:
        # Update status
        active_requests[request_id]["status"] = "running"
        active_requests[request_id]["message"] = "Running lunar pattern analysis..."

        logger.info(f"🚀 Starting backtest {request_id}: {request.symbol} ({request.timing_type})")

        # Create tester with custom parameters
        tester = EnhancedDailyLunarTester(timing_type=request.timing_type)

        # Override thresholds if provided
        if request.accuracy_threshold:
            tester.ACCURACY_THRESHOLD = request.accuracy_threshold
        if request.min_occurrences:
            tester.MIN_OCCURRENCES = request.min_occurrences

        # Run the analysis
        start_time = datetime.now()
        tester.run_analysis(request.symbol, request.market_name)
        execution_time = (datetime.now() - start_time).total_seconds()

        # Get results summary (query the patterns that were just stored)
        cursor = tester.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*), MAX(accuracy_rate),
                   (SELECT pattern_name FROM lunar_patterns
                    WHERE market_symbol = %s AND timing_type = %s
                    ORDER BY accuracy_rate DESC LIMIT 1)
            FROM lunar_patterns
            WHERE market_symbol = %s AND timing_type = %s
        """, (f"{request.market_name}_DAILY", request.timing_type,
              f"{request.market_name}_DAILY", request.timing_type))

        result = cursor.fetchone()
        patterns_found = result[0] if result else 0
        best_accuracy = float(result[1]) if result and result[1] else 0.0
        best_pattern_name = result[2] if result and result[2] else None

        cursor.close()
        tester.conn.close()

        # Update final status
        active_requests[request_id].update({
            "status": "completed",
            "message": f"Analysis completed successfully. Found {patterns_found} patterns.",
            "patterns_found": patterns_found,
            "best_pattern": {
                "name": best_pattern_name,
                "accuracy": best_accuracy
            } if best_pattern_name else None,
            "execution_time": execution_time
        })

        logger.info(f"✅ Completed backtest {request_id}: {patterns_found} patterns found")

    except Exception as e:
        logger.error(f"❌ Backtest {request_id} failed: {e}")
        active_requests[request_id].update({
            "status": "failed",
            "message": f"Analysis failed: {str(e)}"
        })

if __name__ == "__main__":
    # For local development
    uvicorn.run(
        "backtesting_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )