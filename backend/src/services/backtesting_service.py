#!/usr/bin/env python3
"""
Real Backtesting Service

A FastAPI service that accepts backtesting requests and runs real lunar pattern analysis
using the EnhancedDailyLunarTester.

Features:
- Real data validation before analysis
- Integration with EnhancedDailyLunarTester
- Support for same_day, next_day, and all timing types
- Proper error handling and status reporting
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, BackgroundTasks
import psycopg2
import pandas as pd

# Add the analyzer to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'llm_analyzer'))
from enhanced_daily_lunar_tester import EnhancedDailyLunarTester

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Real Backtesting Service",
    description="Lunar pattern backtesting with real market data validation and analysis",
    version="2.0.0"
)

class BacktestRequest(BaseModel):
    symbol: str = Field(..., description="Market symbol (e.g., PLATINUM_FUTURES)")
    market_name: str = Field(..., description="Market name (e.g., PLATINUM)")
    timing_type: str = Field(default="next_day", description="Timing type: same_day, next_day, or all")
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
    data_summary: Optional[Dict[str, Any]] = None

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

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'financial_postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )

def validate_market_data(symbol: str, market_name: str, start_date: str = None, end_date: str = None):
    """Check if market data exists for the given symbol"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check multiple possible symbol formats
    possible_symbols = [
        symbol,
        f"{market_name}_DAILY",
        f"{market_name}_FUTURES",
        f"{symbol}_DAILY",
        market_name
    ]

    data_found = {}
    for sym in possible_symbols:
        # Check market_data table
        cursor.execute("""
            SELECT COUNT(*), MIN(trade_date), MAX(trade_date)
            FROM market_data
            WHERE symbol = %s
        """, (sym,))
        result = cursor.fetchone()

        if result and result[0] > 0:
            data_found[sym] = {
                'table': 'market_data',
                'count': result[0],
                'start_date': result[1],
                'end_date': result[2]
            }

        # Check market_data_intraday table
        cursor.execute("""
            SELECT COUNT(*), MIN(datetime::date), MAX(datetime::date)
            FROM market_data_intraday
            WHERE symbol = %s
        """, (sym,))
        result = cursor.fetchone()

        if result and result[0] > 0:
            data_found[f"{sym}_intraday"] = {
                'table': 'market_data_intraday',
                'count': result[0],
                'start_date': result[1],
                'end_date': result[2]
            }

    cursor.close()
    conn.close()

    return data_found

def validate_astrological_data(start_date: str = None, end_date: str = None):
    """Check if astrological data exists for the date range"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check planetary positions
    cursor.execute("""
        SELECT COUNT(*), MIN(trade_date), MAX(trade_date)
        FROM daily_planetary_positions
    """)
    positions_result = cursor.fetchone()

    # Check planetary aspects
    cursor.execute("""
        SELECT COUNT(*), MIN(trade_date), MAX(trade_date)
        FROM daily_planetary_aspects
    """)
    aspects_result = cursor.fetchone()

    cursor.close()
    conn.close()

    return {
        'planetary_positions': {
            'count': positions_result[0] if positions_result else 0,
            'start_date': positions_result[1] if positions_result else None,
            'end_date': positions_result[2] if positions_result else None
        },
        'planetary_aspects': {
            'count': aspects_result[0] if aspects_result else 0,
            'start_date': aspects_result[1] if aspects_result else None,
            'end_date': aspects_result[2] if aspects_result else None
        }
    }

@app.get("/")
async def root():
    return {
        "service": "Real Backtesting Service",
        "status": "running",
        "version": "2.0.0",
        "active_requests": len(active_requests),
        "features": ["real_analysis", "data_validation", "all_timing_type", "enhanced_daily_lunar_tester"]
    }

@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")

@app.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """Run backtesting analysis with real EnhancedDailyLunarTester"""

    # Validate timing_type
    if request.timing_type not in ['same_day', 'next_day', 'all']:
        raise HTTPException(
            status_code=400,
            detail="timing_type must be 'same_day', 'next_day', or 'all'"
        )

    # Generate request ID
    request_id = f"{request.symbol}_{request.timing_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Pre-validate data availability
    try:
        market_data = validate_market_data(request.symbol, request.market_name, request.start_date, request.end_date)
        astro_data = validate_astrological_data(request.start_date, request.end_date)

        if not market_data:
            return BacktestResponse(
                request_id=request_id,
                status="failed",
                message=f"No market data found for {request.market_name} ({request.symbol}). Available symbols can be checked via /data/summary endpoint.",
                data_summary={
                    "market_data_found": False,
                    "searched_symbols": [request.symbol, f"{request.market_name}_DAILY", f"{request.market_name}_FUTURES"],
                    "astrological_data": astro_data
                }
            )

        # Track request
        active_requests[request_id] = {
            "status": "starting",
            "request": request.dict(),
            "start_time": datetime.now(),
            "data_summary": {
                "market_data": market_data,
                "astrological_data": astro_data
            }
        }

    except Exception as e:
        logger.error(f"Data validation failed: {e}")
        return BacktestResponse(
            request_id=request_id,
            status="failed",
            message=f"Data validation failed: {str(e)}"
        )

    # Run backtest in background
    background_tasks.add_task(execute_real_backtest, request_id, request)

    return BacktestResponse(
        request_id=request_id,
        status="accepted",
        message=f"Real backtesting started for {request.market_name} ({request.timing_type}) with EnhancedDailyLunarTester",
        data_summary=active_requests[request_id]["data_summary"]
    )

@app.get("/backtest/{request_id}", response_model=BacktestResponse)
async def get_backtest_status(request_id: str):
    """Get status of a backtesting request"""

    if request_id not in active_requests:
        raise HTTPException(status_code=404, detail="Request not found")

    request_info = active_requests[request_id]
    return BacktestResponse(
        request_id=request_id,
        status=request_info["status"],
        message=request_info.get("message", ""),
        patterns_found=request_info.get("patterns_found"),
        best_pattern=request_info.get("best_pattern"),
        execution_time_seconds=request_info.get("execution_time"),
        data_summary=request_info.get("data_summary")
    )

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
                "start_time": info["start_time"].isoformat(),
                "has_data": bool(info.get("data_summary", {}).get("market_data"))
            }
            for req_id, info in active_requests.items()
        ]
    }

@app.get("/data/summary")
async def get_data_summary():
    """Get summary of available market and astrological data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get available market symbols
        cursor.execute("""
            SELECT symbol, COUNT(*), MIN(trade_date), MAX(trade_date)
            FROM market_data
            GROUP BY symbol
            ORDER BY symbol
        """)
        market_symbols = [
            {
                "symbol": row[0],
                "count": row[1],
                "start_date": row[2].isoformat() if row[2] else None,
                "end_date": row[3].isoformat() if row[3] else None
            }
            for row in cursor.fetchall()
        ]

        # Get intraday symbols
        cursor.execute("""
            SELECT symbol, COUNT(*), MIN(datetime::date), MAX(datetime::date)
            FROM market_data_intraday
            GROUP BY symbol
            ORDER BY symbol
        """)
        intraday_symbols = [
            {
                "symbol": row[0],
                "count": row[1],
                "start_date": row[2].isoformat() if row[2] else None,
                "end_date": row[3].isoformat() if row[3] else None
            }
            for row in cursor.fetchall()
        ]

        # Get astrological data summary
        astro_data = validate_astrological_data()

        cursor.close()
        conn.close()

        return {
            "market_data": market_symbols,
            "intraday_data": intraday_symbols,
            "astrological_data": astro_data,
            "total_market_symbols": len(market_symbols),
            "total_intraday_symbols": len(intraday_symbols)
        }

    except Exception as e:
        logger.error(f"Failed to get data summary: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/patterns/summary")
async def get_patterns_summary():
    """Get summary of all stored patterns"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
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
        conn.close()

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

async def execute_real_backtest(request_id: str, request: BacktestRequest):
    """Execute real backtesting analysis using EnhancedDailyLunarTester"""
    try:
        active_requests[request_id]["status"] = "running"
        active_requests[request_id]["message"] = "Running real lunar pattern analysis with EnhancedDailyLunarTester..."

        logger.info(f"🚀 Starting REAL backtest {request_id}: {request.symbol} ({request.timing_type})")

        start_time = datetime.now()

        # Validate market data exists
        market_data = validate_market_data(request.symbol, request.market_name)
        if not market_data:
            active_requests[request_id].update({
                "status": "failed",
                "message": f"No market data found for {request.market_name} ({request.symbol}). Cannot perform lunar pattern analysis."
            })
            return

        # Run analysis for each timing type
        timing_types = []
        if request.timing_type == "all":
            timing_types = ["same_day", "next_day"]
        else:
            timing_types = [request.timing_type]

        total_patterns_found = 0
        best_pattern = None
        best_accuracy = 0.0

        for timing_type in timing_types:
            logger.info(f"🌙 Running {timing_type} analysis for {request.market_name}")

            # Create tester with custom parameters
            tester = EnhancedDailyLunarTester(timing_type=timing_type)

            # Override thresholds if provided
            if request.accuracy_threshold:
                tester.ACCURACY_THRESHOLD = request.accuracy_threshold
            if request.min_occurrences:
                tester.MIN_OCCURRENCES = request.min_occurrences

            # Get patterns count before analysis
            cursor = tester.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM lunar_patterns
                WHERE market_symbol = %s AND timing_type = %s
            """, (f"{request.market_name}_DAILY", timing_type))
            patterns_before = cursor.fetchone()[0]

            # Run the REAL analysis
            tester.run_analysis(request.symbol, request.market_name)

            # Get patterns count after analysis
            cursor.execute("""
                SELECT COUNT(*) FROM lunar_patterns
                WHERE market_symbol = %s AND timing_type = %s
            """, (f"{request.market_name}_DAILY", timing_type))
            patterns_after = cursor.fetchone()[0]
            new_patterns = patterns_after - patterns_before

            total_patterns_found += new_patterns

            # Get best pattern for this timing type
            cursor.execute("""
                SELECT pattern_name, accuracy_rate
                FROM lunar_patterns
                WHERE market_symbol = %s AND timing_type = %s
                ORDER BY accuracy_rate DESC LIMIT 1
            """, (f"{request.market_name}_DAILY", timing_type))
            result = cursor.fetchone()

            if result and result[1] > best_accuracy:
                best_accuracy = result[1]
                best_pattern = {
                    "name": result[0],
                    "accuracy": float(result[1]),
                    "timing_type": timing_type
                }

            cursor.close()
            tester.conn.close()

            logger.info(f"✅ Completed {timing_type} analysis: {new_patterns} new patterns found")

        execution_time = (datetime.now() - start_time).total_seconds()

        # Update final status
        active_requests[request_id].update({
            "status": "completed",
            "message": f"Real analysis completed using EnhancedDailyLunarTester. Found {total_patterns_found} new patterns.",
            "patterns_found": total_patterns_found,
            "best_pattern": best_pattern,
            "execution_time": execution_time
        })

        logger.info(f"✅ Completed REAL backtest {request_id}: {total_patterns_found} patterns found")

    except Exception as e:
        logger.error(f"❌ Real backtest {request_id} failed: {e}", exc_info=True)
        active_requests[request_id].update({
            "status": "failed",
            "message": f"Real analysis failed: {str(e)}"
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backtesting_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )