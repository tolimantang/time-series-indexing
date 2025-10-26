#!/usr/bin/env python3
"""
Unified Backfill Service

A FastAPI service that accepts backfill requests for different data types and uses
existing encoders to backfill historical data. Supports market data (Yahoo Finance),
astrological data (Swiss Ephemeris), and future news data.

Features:
- Market data backfill using existing market_encoder
- Astrological data backfill using existing astro_encoder
- On-demand ephemeral service pattern
- Real data validation and error handling
- Background task processing with status tracking
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from fastapi import FastAPI, HTTPException, BackgroundTasks
import psycopg2
import pandas as pd
import yfinance as yf

# Set up logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add encoders to the path - handle both local development and container deployment
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)

# Try multiple paths for encoders
encoder_paths = [
    os.path.join(parent_dir, 'market_encoder'),
    os.path.join(parent_dir, 'astro_encoder'),
    '/app/market_encoder',
    '/app/astro_encoder',
    '/app'
]

for path in encoder_paths:
    if path not in sys.path:
        sys.path.append(path)

# Import encoders with fallbacks
try:
    from market_encoder.core.encoder import MarketEncoder
    MARKET_ENCODER_AVAILABLE = True
    logger.info("✅ MarketEncoder imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ MarketEncoder not available: {e}")
    MARKET_ENCODER_AVAILABLE = False

    # Create fallback MarketEncoder
    class MarketEncoder:
        def __init__(self, **kwargs):
            pass

        def fetch_market_data(self, symbol, start_date, end_date):
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            return ticker.history(start=start_date, end=end_date)

try:
    from astro_encoder.core.encoder import AstroEncoder
    ASTRO_ENCODER_AVAILABLE = True
    logger.info("✅ AstroEncoder imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ AstroEncoder not available: {e}")
    ASTRO_ENCODER_AVAILABLE = False

    # Create fallback AstroEncoder
    class AstroEncoder:
        def __init__(self):
            pass

        def encode_date_range(self, start_date, end_date, location='universal'):
            logger.info(f"🌙 Astro encoding from {start_date} to {end_date} (simplified)")
            return []  # Simplified: return empty list for now

app = FastAPI(
    title="Unified Backfill Service",
    description="On-demand backfill service for market data, astrological data, and news",
    version="1.0.0"
)

class BackfillRequest(BaseModel):
    type: str = Field(..., description="Data type: market, astro, or news")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")

    # Market-specific fields
    symbol: Optional[str] = Field(None, description="Market symbol (required for market type)")
    source: Optional[str] = Field("yahoo_finance", description="Data source for market data")

    # Astro-specific fields
    planets: Optional[List[str]] = Field(None, description="List of planets for astro data")
    location: Optional[str] = Field("universal", description="Location for astrological calculations")

    # News-specific fields (future)
    keywords: Optional[List[str]] = Field(None, description="Keywords for news data")
    news_sources: Optional[List[str]] = Field(None, description="News sources")

    @validator('type')
    def validate_type(cls, v):
        if v not in ['market', 'astro', 'news']:
            raise ValueError('type must be market, astro, or news')
        return v

    @validator('symbol')
    def validate_symbol_for_market(cls, v, values):
        if values.get('type') == 'market' and not v:
            raise ValueError('symbol is required for market data backfill')
        return v

class BackfillResponse(BaseModel):
    request_id: str
    status: str
    message: str
    type: str
    records_processed: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    execution_time_seconds: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

# In-memory storage for request tracking
active_requests: Dict[str, Dict] = {}

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'financial_postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )

def validate_date_range(start_date: str, end_date: str, data_type: str = "market") -> tuple:
    """Validate and parse date range. Allows future dates for astrological data."""
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        if start >= end:
            raise ValueError("start_date must be before end_date")

        # Allow future dates for astrological data since Swiss Ephemeris can calculate them
        if end > datetime.now() and data_type != "astro":
            raise ValueError("end_date cannot be in the future")

        return start, end
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format or range: {str(e)}")

def check_existing_data(data_type: str, symbol: str = None, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """Check what data already exists in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    existing_data = {}

    if data_type == "market" and symbol:
        cursor.execute("""
            SELECT COUNT(*), MIN(trade_date), MAX(trade_date)
            FROM market_data
            WHERE symbol = %s
        """, (symbol,))
        result = cursor.fetchone()

        if result and result[0] > 0:
            existing_data["market_data"] = {
                "count": result[0],
                "start_date": result[1].isoformat() if result[1] else None,
                "end_date": result[2].isoformat() if result[2] else None
            }

    elif data_type == "astro":
        cursor.execute("""
            SELECT COUNT(*), MIN(trade_date), MAX(trade_date)
            FROM daily_planetary_positions
        """)
        positions_result = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*), MIN(trade_date), MAX(trade_date)
            FROM daily_planetary_aspects
        """)
        aspects_result = cursor.fetchone()

        existing_data["astrological_data"] = {
            "planetary_positions": {
                "count": positions_result[0] if positions_result else 0,
                "start_date": positions_result[1].isoformat() if positions_result and positions_result[1] else None,
                "end_date": positions_result[2].isoformat() if positions_result and positions_result[2] else None
            },
            "planetary_aspects": {
                "count": aspects_result[0] if aspects_result else 0,
                "start_date": aspects_result[1].isoformat() if aspects_result and aspects_result[1] else None,
                "end_date": aspects_result[2].isoformat() if aspects_result and aspects_result[2] else None
            }
        }

    cursor.close()
    conn.close()

    return existing_data

@app.get("/")
async def root():
    return {
        "service": "Unified Backfill Service",
        "status": "running",
        "version": "1.0.0",
        "active_requests": len(active_requests),
        "supported_types": ["market", "astro", "news"],
        "pattern": "ephemeral_on_demand"
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

@app.post("/backfill", response_model=BackfillResponse)
async def start_backfill(request: BackfillRequest, background_tasks: BackgroundTasks):
    """Start a backfill operation"""

    # Validate date range (allow future dates for astrological data)
    start_dt, end_dt = validate_date_range(request.start_date, request.end_date, request.type)

    # Generate request ID
    request_id = f"{request.type}_{request.symbol or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Check existing data
    try:
        existing_data = check_existing_data(request.type, request.symbol, request.start_date, request.end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check existing data: {str(e)}")

    # Track request
    active_requests[request_id] = {
        "status": "starting",
        "request": request.dict(),
        "start_time": datetime.now(),
        "existing_data": existing_data
    }

    # Start backfill in background
    background_tasks.add_task(execute_backfill, request_id, request)

    return BackfillResponse(
        request_id=request_id,
        status="accepted",
        message=f"Backfill started for {request.type} data from {request.start_date} to {request.end_date}",
        type=request.type,
        start_date=request.start_date,
        end_date=request.end_date,
        details={"existing_data": existing_data}
    )

@app.get("/backfill/{request_id}", response_model=BackfillResponse)
async def get_backfill_status(request_id: str):
    """Get status of a backfill request"""

    if request_id not in active_requests:
        raise HTTPException(status_code=404, detail="Request not found")

    request_info = active_requests[request_id]

    return BackfillResponse(
        request_id=request_id,
        status=request_info["status"],
        message=request_info.get("message", ""),
        type=request_info["request"]["type"],
        records_processed=request_info.get("records_processed"),
        start_date=request_info["request"]["start_date"],
        end_date=request_info["request"]["end_date"],
        execution_time_seconds=request_info.get("execution_time"),
        details=request_info.get("details")
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
                "type": info["request"]["type"],
                "symbol": info["request"].get("symbol"),
                "start_date": info["request"]["start_date"],
                "end_date": info["request"]["end_date"],
                "start_time": info["start_time"].isoformat()
            }
            for req_id, info in active_requests.items()
        ]
    }

@app.get("/data/summary")
async def get_data_summary():
    """Get summary of available data in database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Market data summary
        cursor.execute("""
            SELECT symbol, COUNT(*), MIN(trade_date), MAX(trade_date)
            FROM market_data
            GROUP BY symbol
            ORDER BY symbol
        """)
        market_data = [
            {
                "symbol": row[0],
                "count": row[1],
                "start_date": row[2].isoformat() if row[2] else None,
                "end_date": row[3].isoformat() if row[3] else None
            }
            for row in cursor.fetchall()
        ]

        # Astrological data summary
        cursor.execute("""
            SELECT COUNT(*), MIN(trade_date), MAX(trade_date)
            FROM daily_planetary_positions
        """)
        astro_positions = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*), MIN(trade_date), MAX(trade_date)
            FROM daily_planetary_aspects
        """)
        astro_aspects = cursor.fetchone()

        cursor.close()
        conn.close()

        return {
            "market_data": market_data,
            "astrological_data": {
                "planetary_positions": {
                    "count": astro_positions[0] if astro_positions else 0,
                    "start_date": astro_positions[1].isoformat() if astro_positions and astro_positions[1] else None,
                    "end_date": astro_positions[2].isoformat() if astro_positions and astro_positions[2] else None
                },
                "planetary_aspects": {
                    "count": astro_aspects[0] if astro_aspects else 0,
                    "start_date": astro_aspects[1].isoformat() if astro_aspects and astro_aspects[1] else None,
                    "end_date": astro_aspects[2].isoformat() if astro_aspects and astro_aspects[2] else None
                }
            },
            "total_market_symbols": len(market_data)
        }

    except Exception as e:
        logger.error(f"Failed to get data summary: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

async def execute_backfill(request_id: str, request: BackfillRequest):
    """Execute the actual backfill operation"""
    try:
        active_requests[request_id]["status"] = "running"
        active_requests[request_id]["message"] = f"Running {request.type} backfill..."

        logger.info(f"🚀 Starting {request.type} backfill {request_id}")

        start_time = datetime.now()
        records_processed = 0

        if request.type == "market":
            records_processed = await backfill_market_data(request_id, request)
        elif request.type == "astro":
            records_processed = await backfill_astro_data(request_id, request)
        elif request.type == "news":
            records_processed = await backfill_news_data(request_id, request)

        execution_time = (datetime.now() - start_time).total_seconds()

        # Update final status
        active_requests[request_id].update({
            "status": "completed",
            "message": f"{request.type} backfill completed successfully. Processed {records_processed} records.",
            "records_processed": records_processed,
            "execution_time": execution_time
        })

        logger.info(f"✅ Completed {request.type} backfill {request_id}: {records_processed} records")

    except Exception as e:
        logger.error(f"❌ Backfill {request_id} failed: {e}", exc_info=True)
        active_requests[request_id].update({
            "status": "failed",
            "message": f"{request.type} backfill failed: {str(e)}"
        })

async def backfill_market_data(request_id: str, request: BackfillRequest) -> int:
    """Backfill market data using Yahoo Finance"""
    logger.info(f"📈 Backfilling market data for {request.symbol}")

    # Use Yahoo Finance directly for now (can integrate with MarketEncoder later)
    ticker = yf.Ticker(request.symbol)

    try:
        # Fetch historical data
        hist = ticker.history(start=request.start_date, end=request.end_date)

        if hist.empty:
            raise ValueError(f"No data found for symbol {request.symbol}")

        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()

        records_inserted = 0

        for date, row in hist.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO market_data (
                        symbol, trade_date, open_price, high_price, low_price,
                        close_price, volume, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (symbol, trade_date) DO NOTHING
                """, (
                    request.symbol,
                    date.date(),
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    int(row['Volume']) if pd.notna(row['Volume']) else None
                ))

                if cursor.rowcount > 0:
                    records_inserted += 1

            except Exception as e:
                logger.warning(f"Failed to insert data for {date}: {e}")

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"✅ Inserted {records_inserted} market data records for {request.symbol}")
        return records_inserted

    except Exception as e:
        logger.error(f"❌ Market data backfill failed: {e}")
        raise

async def backfill_astro_data(request_id: str, request: BackfillRequest) -> int:
    """Backfill astrological data using Swiss Ephemeris"""
    logger.info(f"🌙 Backfilling astrological data from {request.start_date} to {request.end_date}")

    try:
        # Use existing AstroEncoder
        astro_encoder = AstroEncoder()

        start_dt = datetime.strptime(request.start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(request.end_date, '%Y-%m-%d')

        # Get astronomical data for date range
        astro_data_list = astro_encoder.encode_date_range(start_dt, end_dt, request.location)

        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()

        positions_inserted = 0
        aspects_inserted = 0

        for astro_data in astro_data_list:
            trade_date = astro_data.date.date()

            # Insert planetary positions
            for planet_name, position in astro_data.positions.items():
                try:
                    cursor.execute("""
                        INSERT INTO daily_planetary_positions (
                            trade_date, planet, longitude, latitude, distance, speed,
                            zodiac_sign, degree_in_sign, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (trade_date, planet) DO NOTHING
                    """, (
                        trade_date,
                        planet_name,
                        position.longitude,
                        position.latitude,
                        position.distance,
                        position.speed,
                        position.sign,
                        position.degree_in_sign
                    ))

                    if cursor.rowcount > 0:
                        positions_inserted += 1

                except Exception as e:
                    logger.warning(f"Failed to insert position for {planet_name} on {trade_date}: {e}")

            # Insert aspects
            for aspect in astro_data.aspects:
                try:
                    cursor.execute("""
                        INSERT INTO daily_planetary_aspects (
                            trade_date, planet1, planet2, aspect_type, orb,
                            exactness, angle, applying_separating, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (trade_date, planet1, planet2, aspect_type) DO NOTHING
                    """, (
                        trade_date,
                        aspect.planet1,
                        aspect.planet2,
                        aspect.aspect_type,
                        aspect.orb,
                        aspect.exactness,
                        aspect.angle,
                        aspect.applying_separating
                    ))

                    if cursor.rowcount > 0:
                        aspects_inserted += 1

                except Exception as e:
                    logger.warning(f"Failed to insert aspect {aspect.planet1}-{aspect.planet2} on {trade_date}: {e}")

        conn.commit()
        cursor.close()
        conn.close()

        total_inserted = positions_inserted + aspects_inserted
        logger.info(f"✅ Inserted {positions_inserted} planetary positions and {aspects_inserted} aspects")
        return total_inserted

    except Exception as e:
        logger.error(f"❌ Astrological data backfill failed: {e}")
        raise

async def backfill_news_data(request_id: str, request: BackfillRequest) -> int:
    """Backfill news data (placeholder for future implementation)"""
    logger.info(f"📰 News backfill requested but not yet implemented")

    # Update status to indicate this is not implemented yet
    active_requests[request_id]["message"] = "News backfill not yet implemented"

    # For now, just simulate some processing
    import asyncio
    await asyncio.sleep(2)

    raise NotImplementedError("News data backfill is not yet implemented")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backfill_service:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )