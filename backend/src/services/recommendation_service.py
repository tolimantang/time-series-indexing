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
    planetary_positions: Dict[str, Dict[str, Any]] = {}  # All planetary positions for pattern matching
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

        logger.info(f"🔍 Matching astro data: positions={list(astro_data.get('positions', {}).keys())}, aspects_count={len(astro_data.get('aspects', []))}")

        if not astro_data:
            logger.info("❌ No astro data provided")
            return matches

        logger.info(f"🔍 Checking {len(patterns)} patterns for matches")

        for i, pattern in enumerate(patterns):
            # Log first few patterns to understand structure
            if i < 3:
                logger.info(f"🔍 Pattern {i+1}: {pattern.get('pattern_name', 'Unknown')} - keys: {list(pattern.keys())}")

            # Calculate match quality based on pattern components
            match_score = self._calculate_pattern_match(astro_data, pattern)

            if i < 3:
                logger.info(f"🔍 Pattern {i+1} match score: {match_score:.3f}")

            if match_score > 0.5:  # Minimum 50% match
                quality = "exact" if match_score > 0.9 else "close" if match_score > 0.7 else "partial"

                logger.info(f"✅ MATCH: {pattern['pattern_name']} - score: {match_score:.3f}, quality: {quality}")

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

    def scan_forecast_for_patterns(self, astro_forecast: List[AstroCondition], patterns: List[Dict]) -> List[Dict]:
        """Scan entire forecast period for upcoming pattern matches"""
        upcoming_signals = []

        for day_forecast in astro_forecast:
            # Convert forecast to astro_data format using complete planetary positions
            astro_data = {
                'positions': day_forecast.planetary_positions,
                'aspects': day_forecast.aspects
            }

            # Enhanced logging for key dates
            moon_aspects = [a for a in day_forecast.aspects if a.get('planet1') == 'moon' or a.get('planet2') == 'moon']
            pluto_aspects = [a for a in day_forecast.aspects if 'pluto' in [a.get('planet1'), a.get('planet2')]]

            if day_forecast.date in ['2025-10-28', '2025-10-29'] or len(pluto_aspects) > 0:
                logger.info(f"🔍 Scanning {day_forecast.date}: Moon in {day_forecast.moon_sign}")
                moon_aspect_list = [f"{a.get('planet1')}-{a.get('planet2')} {a.get('aspect_type')}" for a in moon_aspects]
                pluto_aspect_list = [f"{a.get('planet1')}-{a.get('planet2')} {a.get('aspect_type')}" for a in pluto_aspects]
                logger.info(f"   🌙 Moon aspects: {moon_aspect_list}")
                logger.info(f"   🪐 Pluto aspects: {pluto_aspect_list}")

            # Find patterns for this day
            day_matches = self.match_astro_to_patterns(astro_data, patterns)

            if day_matches:
                logger.info(f"🎯 Found {len(day_matches)} pattern matches for {day_forecast.date}")
                for match in day_matches:
                    logger.info(f"   📊 {match.pattern_name}: {match.confidence_score:.1%} confidence ({match.prediction} {match.timing_type})")

                    upcoming_signals.append({
                        'date': day_forecast.date,
                        'pattern': match,
                        'moon_sign': day_forecast.moon_sign,
                        'aspects_count': len(day_forecast.aspects)
                    })

        return upcoming_signals

    def _calculate_pattern_match(self, astro_data: Dict, pattern: Dict) -> float:
        """Calculate how well current astro conditions match a historical pattern"""
        score = 0.0
        total_factors = 0

        # Check Moon sign match
        moon_position = astro_data.get('positions', {}).get('moon', {})
        pattern_moon_sign = pattern.get('moon_sign')
        actual_moon_sign = moon_position.get('sign') if moon_position else None

        if moon_position and pattern_moon_sign:
            total_factors += 1
            if actual_moon_sign and actual_moon_sign.lower() == pattern_moon_sign.lower():
                score += 0.4  # Moon sign is important
                logger.info(f"🌙 Moon sign MATCH: {actual_moon_sign} == {pattern_moon_sign}")
            else:
                logger.info(f"🌙 Moon sign mismatch: {actual_moon_sign} != {pattern_moon_sign}")

        # Check aspects match
        aspects = astro_data.get('aspects', [])
        pattern_aspect = pattern.get('aspect_type')
        pattern_target = pattern.get('target_planet')

        moon_aspects = [a for a in aspects if a.get('planet1') == 'moon' or a.get('planet2') == 'moon']
        aspect_descriptions = [f"{a.get('planet1')}-{a.get('planet2')} {a.get('aspect_type')}" for a in moon_aspects[:3]]
        logger.info(f"🔗 Found {len(moon_aspects)} Moon aspects: {aspect_descriptions}")

        for aspect in aspects:
            if (aspect.get('planet1') == 'moon' and
                aspect.get('aspect_type') == pattern_aspect and
                aspect.get('planet2') == pattern_target):
                total_factors += 1
                score += 0.6  # Exact aspect match is very important
                logger.info(f"🎯 Aspect MATCH: Moon {pattern_aspect} {pattern_target}")

                # Bonus for target planet sign match
                target_positions = astro_data.get('positions', {}).get(aspect.get('planet2'), {})
                pattern_target_sign = pattern.get('target_sign')
                actual_target_sign = target_positions.get('sign') if target_positions else None

                if target_positions and actual_target_sign and pattern_target_sign and actual_target_sign.lower() == pattern_target_sign.lower():
                    score += 0.3
                    logger.info(f"🪐 Target planet sign MATCH: {pattern_target} in {actual_target_sign}")
                else:
                    logger.info(f"🪐 Target planet sign mismatch: {pattern_target} in {actual_target_sign} != {pattern_target_sign}")

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

                    # Extract ALL planetary positions for pattern matching
                    planetary_positions = {}
                    if astro_data.positions:
                        for planet_name, position in astro_data.positions.items():
                            planetary_positions[planet_name] = {
                                'sign': position.sign,
                                'longitude': position.longitude,
                                'degree_in_sign': position.degree_in_sign
                            }

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
                        planetary_positions=planetary_positions,
                        aspects=aspects,
                        significant_events=astro_data.significant_events or []
                    ))

            except Exception as e:
                logger.warning(f"Failed to get astro data for {current_date}: {e}")

            current_date += timedelta(days=1)

        return forecast

class LLMRecommendationEngine:
    """Generate intelligent recommendations using pattern matches and astro forecast"""

    def __init__(self):
        self.conn = get_db_connection()

    def get_cross_asset_insights(self, current_astro_dict: Dict, min_accuracy: float = 0.70) -> List[str]:
        """Get insights from related markets with similar astrological conditions"""
        insights = []

        # Define related asset groups
        asset_groups = {
            'precious_metals': ['GOLD_DAILY', 'PLATINUM_DAILY', 'SILVER_DAILY'],
            'energy': ['OIL_DAILY', 'NATURAL_GAS_DAILY'],
            'currencies': ['EUR_USD_DAILY', 'GBP_USD_DAILY', 'USD_JPY_DAILY']
        }

        # Get patterns from all markets
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT market_symbol, pattern_name, accuracy_rate, prediction, timing_type,
                   aspect_type, moon_sign, target_planet
            FROM lunar_patterns
            WHERE accuracy_rate >= %s
            ORDER BY accuracy_rate DESC
            LIMIT 50
        """, (min_accuracy,))

        all_patterns = cursor.fetchall()
        cursor.close()

        # Group patterns by market category
        for group_name, markets in asset_groups.items():
            group_patterns = [p for p in all_patterns if p[0] in markets]
            if not group_patterns:
                continue

            # Check if current conditions match any patterns in this group
            matching_patterns = []
            for pattern in group_patterns:
                # Simple pattern matching logic
                if current_astro_dict and current_astro_dict.get('aspects'):
                    for aspect in current_astro_dict['aspects']:
                        if (aspect.get('planet1') == 'moon' and
                            aspect.get('aspect_type') == pattern[5] and
                            aspect.get('planet2') == pattern[7]):
                            matching_patterns.append(pattern)
                            break

            if matching_patterns:
                best_pattern = max(matching_patterns, key=lambda x: x[2])  # highest accuracy
                market_name = best_pattern[0].replace('_DAILY', '')
                prediction = best_pattern[3]
                accuracy = best_pattern[2]

                insights.append(f"{group_name.title()}: {market_name} shows {prediction} signals "
                             f"with {accuracy:.1%} accuracy under similar conditions")

        return insights

    def generate_recommendation(
        self,
        symbol: str,
        pattern_matches: List[PatternMatch],
        astro_forecast: List[AstroCondition],
        current_astro_dict: Dict = None,
        upcoming_signals: List[Dict] = None,
        market_context: Dict = None
    ) -> Recommendation:
        """Generate recommendation based on patterns and forecast"""

        # Get cross-asset insights
        cross_asset_insights = self.get_cross_asset_insights(current_astro_dict)

        # Check for upcoming signals even if no immediate patterns
        upcoming_alerts = []
        if upcoming_signals:
            for signal in upcoming_signals[:3]:  # Top 3 upcoming signals
                pattern = signal['pattern']
                upcoming_alerts.append(f"{signal['date']}: {pattern.pattern_name} "
                                     f"({pattern.confidence_score:.1%} confidence, {pattern.prediction} {pattern.timing_type})")

        if not pattern_matches:
            base_reasoning = "No significant astrological patterns detected for today"
            if upcoming_alerts:
                base_reasoning += f". However, upcoming signals detected: {'; '.join(upcoming_alerts[:2])}"
            elif cross_asset_insights:
                base_reasoning += f". Cross-asset analysis shows: {'; '.join(cross_asset_insights[:2])}"

            # Upgrade action if strong upcoming signals exist
            if upcoming_signals and any(s['pattern'].confidence_score > 0.7 for s in upcoming_signals[:3]):
                action = "WATCH"  # New action type for upcoming opportunities
                confidence = 0.5
            else:
                action = "HOLD"
                confidence = 0.1

            return Recommendation(
                action=action,
                symbol=symbol,
                confidence=confidence,
                reasoning=base_reasoning,
                supporting_patterns=[],
                alternative_scenarios=cross_asset_insights + upcoming_alerts
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

            # Add cross-asset context if available
            if cross_asset_insights:
                reasoning += f" Cross-asset analysis supports this with similar patterns in related markets."

        else:
            action = "HOLD"
            confidence = 0.3
            entry_date = None
            exit_date = None
            reasoning = f"Weak pattern signals detected. Best match: {top_pattern.pattern_name} with {top_pattern.confidence_score:.1%} confidence."

            # Add cross-asset insights to reasoning
            if cross_asset_insights:
                reasoning += f" Cross-asset insights: {'; '.join(cross_asset_insights[:2])}"

        return Recommendation(
            action=action,
            symbol=symbol,
            entry_date=entry_date,
            exit_date=exit_date,
            confidence=confidence,
            reasoning=reasoning,
            supporting_patterns=pattern_matches[:3],  # Top 3 patterns
            alternative_scenarios=cross_asset_insights
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
        logger.info(f"🎯 Found {len(pattern_matches)} pattern matches for today")

        # Get forecast
        astro_forecast = astro_calculator.get_astro_forecast(today, request.forecast_days)
        logger.info(f"🔮 Generated {len(astro_forecast)} days of astrological forecast")

        # Scan entire forecast for upcoming patterns
        upcoming_signals = pattern_matcher.scan_forecast_for_patterns(astro_forecast, patterns)
        logger.info(f"📅 Scanned forecast: found {len(upcoming_signals)} upcoming pattern signals")

        # Generate recommendation
        primary_recommendation = llm_engine.generate_recommendation(
            request.symbol, pattern_matches, astro_forecast, current_astro_dict, upcoming_signals
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