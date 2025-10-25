#!/usr/bin/env python3
"""
Recommendation Service

Provides trading recommendations based on astrological patterns, combining:
- Validated lunar patterns from backtesting results
- Current and future astrological conditions (30-day forecast)
- LLM-powered reasoning for strategic recommendations

Features:
- Pattern matching against historical lunar patterns
- 30-day astrological forecast
- AI-powered recommendation synthesis
- Position entry/exit timing suggestions
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, BackgroundTasks
import json

# Add encoders to the path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)

encoder_paths = [
    os.path.join(parent_dir, 'astro_encoder'),
    '/app/astro_encoder',
    '/app'
]

for path in encoder_paths:
    if path not in sys.path:
        sys.path.append(path)

# Import astro encoder with fallback
try:
    from astro_encoder.core.encoder import AstroEncoder
    ASTRO_ENCODER_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ AstroEncoder imported successfully")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ AstroEncoder not available: {e}")
    ASTRO_ENCODER_AVAILABLE = False

    class AstroEncoder:
        def __init__(self):
            pass
        def encode_date(self, date, location='universal'):
            return None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading Recommendation Service",
    description="AI-powered trading recommendations based on astrological patterns",
    version="1.0.0"
)

class RecommendationRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., GC=F)")
    market_name: str = Field(..., description="Market name for pattern lookup")
    forecast_days: int = Field(30, description="Days to forecast ahead")
    min_accuracy: float = Field(0.70, description="Minimum pattern accuracy threshold")

class PatternMatch(BaseModel):
    pattern_name: str
    accuracy_rate: float
    total_occurrences: int
    prediction: str  # "up" or "down"
    timing_type: str  # "same_day" or "next_day"
    confidence_score: float
    match_quality: str  # "exact", "close", "partial"

class AstroCondition(BaseModel):
    date: str
    moon_sign: Optional[str] = None
    aspects: List[Dict[str, Any]] = []
    significant_events: List[str] = []

class Recommendation(BaseModel):
    action: str  # "LONG", "SHORT", "HOLD", "EXIT"
    symbol: str
    entry_date: Optional[str] = None
    exit_date: Optional[str] = None
    confidence: float
    reasoning: str
    supporting_patterns: List[PatternMatch]
    alternative_scenarios: List[str] = []

class RecommendationResponse(BaseModel):
    request_id: str
    symbol: str
    market_name: str
    timestamp: str
    primary_recommendation: Recommendation
    alternative_recommendations: List[Recommendation] = []
    astro_forecast: List[AstroCondition]
    pattern_matches: List[PatternMatch]
    execution_time_seconds: float

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'financial_postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )

class PatternMatcher:
    """Matches current/future astro conditions against validated lunar patterns"""

    def __init__(self):
        self.conn = get_db_connection()

    def get_validated_patterns(self, market_symbol: str, min_accuracy: float = 0.70) -> List[Dict]:
        """Get all validated patterns for a market above accuracy threshold"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                pattern_name, accuracy_rate, total_occurrences, prediction,
                timing_type, aspect_type, moon_sign, target_planet, target_sign,
                avg_up_move, avg_down_move, expected_return
            FROM lunar_patterns
            WHERE market_symbol = %s
            AND accuracy_rate >= %s
            ORDER BY accuracy_rate DESC, total_occurrences DESC
        """, (market_symbol, min_accuracy))

        results = cursor.fetchall()
        cursor.close()

        patterns = []
        for row in results:
            patterns.append({
                'pattern_name': row[0],
                'accuracy_rate': float(row[1]),
                'total_occurrences': row[2],
                'prediction': row[3],
                'timing_type': row[4],
                'aspect_type': row[5],
                'moon_sign': row[6],
                'target_planet': row[7],
                'target_sign': row[8],
                'avg_up_move': float(row[9]) if row[9] else 0.0,
                'avg_down_move': float(row[10]) if row[10] else 0.0,
                'expected_return': float(row[11]) if row[11] else 0.0
            })

        return patterns

    def match_astro_to_patterns(self, astro_data: Dict, patterns: List[Dict]) -> List[PatternMatch]:
        """Match current astrological conditions to historical patterns"""
        matches = []

        if not astro_data or not astro_data.get('aspects'):
            return matches

        for pattern in patterns:
            # Calculate match quality based on pattern components
            match_score = self._calculate_pattern_match(astro_data, pattern)

            if match_score > 0.5:  # Minimum 50% match
                quality = "exact" if match_score > 0.9 else "close" if match_score > 0.7 else "partial"

                matches.append(PatternMatch(
                    pattern_name=pattern['pattern_name'],
                    accuracy_rate=pattern['accuracy_rate'],
                    total_occurrences=pattern['total_occurrences'],
                    prediction=pattern['prediction'],
                    timing_type=pattern['timing_type'],
                    confidence_score=match_score * pattern['accuracy_rate'],
                    match_quality=quality
                ))

        # Sort by confidence score
        matches.sort(key=lambda x: x.confidence_score, reverse=True)
        return matches

    def _calculate_pattern_match(self, astro_data: Dict, pattern: Dict) -> float:
        """Calculate how well current astro conditions match a historical pattern"""
        score = 0.0
        total_factors = 0

        # Check Moon sign match
        moon_position = astro_data.get('positions', {}).get('moon', {})
        if moon_position and pattern.get('moon_sign'):
            total_factors += 1
            if moon_position.get('sign') == pattern['moon_sign']:
                score += 0.4  # Moon sign is important

        # Check aspects match
        aspects = astro_data.get('aspects', [])
        for aspect in aspects:
            if (aspect.get('planet1') == 'moon' and
                aspect.get('aspect_type') == pattern.get('aspect_type') and
                aspect.get('planet2') == pattern.get('target_planet')):
                total_factors += 1
                score += 0.6  # Exact aspect match is very important

                # Bonus for target planet sign match
                target_positions = astro_data.get('positions', {}).get(aspect.get('planet2'), {})
                if target_positions and target_positions.get('sign') == pattern.get('target_sign'):
                    score += 0.3

        return score / max(total_factors, 1) if total_factors > 0 else 0.0

class AstroCalculator:
    """Calculate current and future astrological conditions"""

    def __init__(self):
        if ASTRO_ENCODER_AVAILABLE:
            self.encoder = AstroEncoder()
        else:
            self.encoder = None

    def get_astro_forecast(self, start_date: datetime, days: int = 30) -> List[AstroCondition]:
        """Get astrological conditions for the next N days"""
        if not self.encoder:
            logger.warning("AstroEncoder not available, returning empty forecast")
            return []

        forecast = []
        current_date = start_date

        for _ in range(days):
            try:
                astro_data = self.encoder.encode_date(current_date)

                if astro_data:
                    # Extract moon sign
                    moon_sign = None
                    if astro_data.positions and 'moon' in astro_data.positions:
                        moon_sign = astro_data.positions['moon'].sign

                    # Extract aspects
                    aspects = []
                    if astro_data.aspects:
                        for aspect in astro_data.aspects:
                            aspects.append({
                                'planet1': aspect.planet1,
                                'planet2': aspect.planet2,
                                'aspect_type': aspect.aspect_type,
                                'orb': aspect.orb,
                                'exactness': aspect.exactness
                            })

                    forecast.append(AstroCondition(
                        date=current_date.strftime('%Y-%m-%d'),
                        moon_sign=moon_sign,
                        aspects=aspects,
                        significant_events=astro_data.significant_events or []
                    ))

            except Exception as e:
                logger.warning(f"Failed to get astro data for {current_date}: {e}")

            current_date += timedelta(days=1)

        return forecast

class LLMRecommendationEngine:
    """Generate intelligent recommendations using pattern matches and astro forecast"""

    def generate_recommendation(
        self,
        symbol: str,
        pattern_matches: List[PatternMatch],
        astro_forecast: List[AstroCondition],
        market_context: Dict = None
    ) -> Recommendation:
        """Generate recommendation based on patterns and forecast"""

        if not pattern_matches:
            return Recommendation(
                action="HOLD",
                symbol=symbol,
                confidence=0.1,
                reasoning="No significant astrological patterns detected above threshold",
                supporting_patterns=[]
            )

        # Analyze top patterns
        top_pattern = pattern_matches[0]

        # Simple rule-based logic (can be enhanced with actual LLM later)
        if top_pattern.confidence_score > 0.8:
            action = "LONG" if top_pattern.prediction == "up" else "SHORT"
            confidence = min(top_pattern.confidence_score, 0.95)

            # Calculate timing
            entry_date = datetime.now().strftime('%Y-%m-%d')
            exit_date = None

            if top_pattern.timing_type == "same_day":
                exit_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            else:  # next_day
                exit_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')

            reasoning = f"""
Based on pattern '{top_pattern.pattern_name}' with {top_pattern.accuracy_rate:.1%} historical accuracy
({top_pattern.total_occurrences} occurrences). Current astrological conditions show a {top_pattern.match_quality}
match to this pattern, suggesting {top_pattern.prediction} movement with {top_pattern.timing_type} timing.
            """.strip()

        else:
            action = "HOLD"
            confidence = 0.3
            entry_date = None
            exit_date = None
            reasoning = f"Weak pattern signals detected. Best match: {top_pattern.pattern_name} with {top_pattern.confidence_score:.1%} confidence."

        return Recommendation(
            action=action,
            symbol=symbol,
            entry_date=entry_date,
            exit_date=exit_date,
            confidence=confidence,
            reasoning=reasoning,
            supporting_patterns=pattern_matches[:3]  # Top 3 patterns
        )

@app.get("/")
async def root():
    return {
        "service": "Trading Recommendation Service",
        "status": "running",
        "version": "1.0.0",
        "features": ["lunar_pattern_matching", "astro_forecasting", "ai_recommendations"],
        "astro_encoder": "available" if ASTRO_ENCODER_AVAILABLE else "fallback"
    }

@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {"status": "healthy", "database": "connected", "astro_encoder": ASTRO_ENCODER_AVAILABLE}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")

@app.post("/recommend", response_model=RecommendationResponse)
async def get_recommendation(request: RecommendationRequest):
    """Generate trading recommendation based on astrological patterns"""

    start_time = datetime.now()
    request_id = f"{request.symbol}_rec_{start_time.strftime('%Y%m%d_%H%M%S')}"

    logger.info(f"🔮 Generating recommendation for {request.symbol} ({request.market_name})")

    try:
        # Initialize components
        pattern_matcher = PatternMatcher()
        astro_calculator = AstroCalculator()
        llm_engine = LLMRecommendationEngine()

        # Get validated patterns
        market_symbol = f"{request.market_name}_DAILY"
        patterns = pattern_matcher.get_validated_patterns(market_symbol, request.min_accuracy)
        logger.info(f"📊 Found {len(patterns)} validated patterns above {request.min_accuracy:.1%} accuracy")

        # Get current astrological conditions
        today = datetime.now()
        current_astro = astro_calculator.encoder.encode_date(today) if astro_calculator.encoder else None

        # Match current conditions to patterns
        current_astro_dict = {}
        if current_astro:
            current_astro_dict = {
                'positions': {name: {'sign': pos.sign} for name, pos in current_astro.positions.items()},
                'aspects': [{'planet1': a.planet1, 'planet2': a.planet2, 'aspect_type': a.aspect_type}
                          for a in current_astro.aspects]
            }

        pattern_matches = pattern_matcher.match_astro_to_patterns(current_astro_dict, patterns)
        logger.info(f"🎯 Found {len(pattern_matches)} pattern matches")

        # Get forecast
        astro_forecast = astro_calculator.get_astro_forecast(today, request.forecast_days)
        logger.info(f"🔮 Generated {len(astro_forecast)} days of astrological forecast")

        # Generate recommendation
        primary_recommendation = llm_engine.generate_recommendation(
            request.symbol, pattern_matches, astro_forecast
        )

        execution_time = (datetime.now() - start_time).total_seconds()

        logger.info(f"✅ Generated recommendation: {primary_recommendation.action} with {primary_recommendation.confidence:.1%} confidence")

        return RecommendationResponse(
            request_id=request_id,
            symbol=request.symbol,
            market_name=request.market_name,
            timestamp=datetime.now().isoformat(),
            primary_recommendation=primary_recommendation,
            astro_forecast=astro_forecast,
            pattern_matches=pattern_matches,
            execution_time_seconds=execution_time
        )

    except Exception as e:
        logger.error(f"❌ Recommendation generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendation: {str(e)}")

@app.get("/patterns/{market_name}")
async def get_market_patterns(market_name: str, min_accuracy: float = 0.70):
    """Get all validated patterns for a market"""
    try:
        pattern_matcher = PatternMatcher()
        market_symbol = f"{market_name}_DAILY"
        patterns = pattern_matcher.get_validated_patterns(market_symbol, min_accuracy)

        return {
            "market_name": market_name,
            "min_accuracy": min_accuracy,
            "total_patterns": len(patterns),
            "patterns": patterns
        }
    except Exception as e:
        logger.error(f"Failed to get patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)