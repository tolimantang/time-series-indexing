"""
Daily trading recommendations engine.
Matches current astrological conditions against historical insights to generate trading recommendations.
"""

import os
import json
import logging
import psycopg2
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from .daily_conditions import DailyAstrologyCalculator

logger = logging.getLogger(__name__)


class DailyTradingEngine:
    """Generate daily trading recommendations based on astrological conditions and insights."""

    def __init__(self, db_config: Optional[Dict[str, str]] = None):
        """Initialize with database configuration."""
        self.db_config = db_config or {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
        }
        self.astro_calculator = DailyAstrologyCalculator(db_config)

        # Oil symbols to analyze
        self.oil_symbols = ['CL', 'BZ', 'HO', 'RB', 'NG']  # Crude, Brent, Heating Oil, Gasoline, Natural Gas

        logger.info("✅ Daily Trading Engine initialized")

    def get_daily_conditions(self, target_date: date) -> Optional[Dict[str, Any]]:
        """Get daily astrological conditions from database."""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT trade_date, planetary_positions, major_aspects, lunar_phase_name,
                       lunar_phase_angle, significant_events, daily_score, market_outlook
                FROM daily_astrological_conditions
                WHERE trade_date = %s
            """, (target_date,))

            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if not row:
                # Calculate and store if not exists
                logger.info(f"📅 No conditions found for {target_date}, calculating...")
                conditions = self.astro_calculator.calculate_daily_conditions(target_date)
                if 'error' not in conditions:
                    self.astro_calculator.store_daily_conditions(conditions)
                    return conditions
                return None

            return {
                'trade_date': row[0],
                'planetary_positions': row[1],
                'major_aspects': row[2],
                'lunar_phase_name': row[3],
                'lunar_phase_angle': row[4],
                'significant_events': row[5],
                'daily_score': row[6],
                'market_outlook': row[7]
            }

        except Exception as e:
            logger.error(f"❌ Error getting daily conditions: {e}")
            return None

    def get_relevant_insights(self, conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get astrological insights relevant to current conditions."""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Get all insights ordered by confidence
            cursor.execute("""
                SELECT id, insight_type, category, pattern_name, description,
                       confidence_score, success_rate, avg_profit, trade_count, evidence
                FROM astrological_insights
                WHERE confidence_score IS NOT NULL
                ORDER BY confidence_score DESC, success_rate DESC
            """)

            all_insights = []
            for row in cursor.fetchall():
                all_insights.append({
                    'id': row[0],
                    'insight_type': row[1],
                    'category': row[2],
                    'pattern_name': row[3],
                    'description': row[4],
                    'confidence_score': row[5],
                    'success_rate': row[6],
                    'avg_profit': row[7],
                    'trade_count': row[8],
                    'evidence': row[9]
                })

            cursor.close()
            conn.close()

            # Filter insights based on current conditions
            relevant_insights = self.filter_relevant_insights(all_insights, conditions)

            logger.info(f"📊 Found {len(relevant_insights)} relevant insights for {conditions['trade_date']}")
            return relevant_insights

        except Exception as e:
            logger.error(f"❌ Error getting insights: {e}")
            return []

    def filter_relevant_insights(self, insights: List[Dict[str, Any]],
                                conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter insights based on current astrological conditions."""
        relevant = []

        lunar_phase = conditions.get('lunar_phase_name', '').lower()
        aspects = conditions.get('major_aspects', [])
        significant_events = conditions.get('significant_events', [])

        for insight in insights:
            relevance_score = 0
            category = insight.get('category', '').lower()
            description = insight.get('description', '').lower()

            # Lunar phase matching
            if category == 'lunar_phase' and lunar_phase:
                if any(phase in description for phase in [lunar_phase, lunar_phase.split()[0]]):
                    relevance_score += 20

            # Planetary aspect matching
            elif category == 'planetary_aspect':
                for aspect in aspects:
                    planet1 = aspect.get('planet1', '').lower()
                    planet2 = aspect.get('planet2', '').lower()
                    aspect_type = aspect.get('aspect', '').lower()

                    if (planet1 in description or planet2 in description) and aspect_type in description:
                        relevance_score += 15
                        if aspect.get('exact', False):
                            relevance_score += 10

            # Seasonal/zodiac matching
            elif category == 'seasonal':
                # Check if any planets are in relevant signs mentioned in description
                positions = conditions.get('planetary_positions', {})
                for planet, pos in positions.items():
                    if isinstance(pos, dict) and 'sign' in pos:
                        if pos['sign'].lower() in description:
                            relevance_score += 10

            # Trading action insights are always somewhat relevant
            elif category == 'trading_action':
                relevance_score += 5

            # Boost for high-confidence insights
            confidence = insight.get('confidence_score', 0)
            if confidence >= 70:
                relevance_score += 10
            elif confidence >= 50:
                relevance_score += 5

            # Only include insights with some relevance
            if relevance_score >= 10:
                insight['relevance_score'] = relevance_score
                relevant.append(insight)

        # Sort by relevance score
        relevant.sort(key=lambda x: x['relevance_score'], reverse=True)

        return relevant[:20]  # Top 20 most relevant

    def generate_symbol_recommendation(self, symbol: str, conditions: Dict[str, Any],
                                     insights: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate recommendation for a specific symbol."""
        try:
            daily_score = conditions.get('daily_score', 50)
            market_outlook = conditions.get('market_outlook', 'neutral')
            lunar_phase = conditions.get('lunar_phase_name', '')

            # Calculate base recommendation
            if daily_score >= 70 and market_outlook in ['bullish', 'neutral']:
                base_recommendation = 'enter_long'
                base_confidence = min(85, daily_score + 10)
            elif daily_score <= 30 and market_outlook in ['bearish', 'volatile']:
                base_recommendation = 'enter_short'
                base_confidence = min(85, (100 - daily_score) + 10)
            elif market_outlook == 'volatile':
                base_recommendation = 'avoid'
                base_confidence = 60
            else:
                base_recommendation = 'hold'
                base_confidence = 40

            # Adjust based on insights
            long_bias = 0
            short_bias = 0
            avoid_bias = 0
            confidence_adjustment = 0

            for insight in insights[:10]:  # Top 10 insights
                relevance = insight.get('relevance_score', 0)
                weight = relevance / 100

                description = insight.get('description', '').lower()
                avg_profit = insight.get('avg_profit', 0)

                # Look for directional signals
                if any(term in description for term in ['long', 'buy', 'enter', 'rise', 'increase']):
                    long_bias += weight * (1 + avg_profit / 100)
                elif any(term in description for term in ['short', 'sell', 'fall', 'decrease', 'decline']):
                    short_bias += weight * (1 + avg_profit / 100)
                elif any(term in description for term in ['avoid', 'risk', 'volatile', 'uncertain']):
                    avoid_bias += weight

                # Confidence adjustment based on insight quality
                if insight.get('confidence_score', 0) >= 70:
                    confidence_adjustment += 5
                elif insight.get('success_rate', 0) >= 70:
                    confidence_adjustment += 3

            # Final recommendation logic
            if long_bias > short_bias + 0.5 and long_bias > avoid_bias:
                final_recommendation = 'enter_long'
                final_confidence = min(90, base_confidence + confidence_adjustment + int(long_bias * 10))
            elif short_bias > long_bias + 0.5 and short_bias > avoid_bias:
                final_recommendation = 'enter_short'
                final_confidence = min(90, base_confidence + confidence_adjustment + int(short_bias * 10))
            elif avoid_bias > 0.8:
                final_recommendation = 'avoid'
                final_confidence = min(85, 50 + int(avoid_bias * 20))
            else:
                final_recommendation = base_recommendation
                final_confidence = max(30, base_confidence + confidence_adjustment)

            # Generate reasoning
            reasoning_parts = [
                f"Daily astrological score: {daily_score}/100 ({market_outlook} outlook)",
                f"Lunar phase: {lunar_phase}"
            ]

            if insights:
                top_insight = insights[0]
                reasoning_parts.append(f"Key insight: {top_insight['description'][:100]}...")

            reasoning = ". ".join(reasoning_parts)

            # Calculate target and stop loss (simplified)
            if final_recommendation in ['enter_long', 'enter_short']:
                holding_period = max(1, min(10, int(daily_score / 10)))  # 1-10 days based on score
            else:
                holding_period = 1

            return {
                'symbol': symbol,
                'recommendation_type': final_recommendation,
                'confidence': final_confidence,
                'astrological_reasoning': reasoning,
                'supporting_insights': [insight['id'] for insight in insights[:5]],
                'holding_period_days': holding_period,
                'daily_conditions_score': daily_score,
                'market_outlook': market_outlook
            }

        except Exception as e:
            logger.error(f"❌ Error generating recommendation for {symbol}: {e}")
            return None

    def generate_daily_recommendations(self, target_date: date) -> Dict[str, Any]:
        """Generate complete set of daily trading recommendations."""
        logger.info(f"🎯 Generating trading recommendations for {target_date}")

        # Get daily conditions
        conditions = self.get_daily_conditions(target_date)
        if not conditions:
            return {'error': 'Failed to get astrological conditions'}

        # Get relevant insights
        insights = self.get_relevant_insights(conditions)
        if not insights:
            logger.warning("⚠️ No relevant insights found, generating basic recommendations")

        recommendations = []

        # Generate recommendations for each oil symbol
        for symbol in self.oil_symbols:
            recommendation = self.generate_symbol_recommendation(symbol, conditions, insights)
            if recommendation:
                recommendations.append(recommendation)

        # Store recommendations in database
        stored_count = self.store_recommendations(target_date, recommendations)

        summary = {
            'recommendation_date': target_date,
            'total_symbols': len(self.oil_symbols),
            'recommendations_generated': len(recommendations),
            'recommendations_stored': stored_count,
            'daily_conditions': {
                'score': conditions.get('daily_score'),
                'outlook': conditions.get('market_outlook'),
                'lunar_phase': conditions.get('lunar_phase_name')
            },
            'insights_used': len(insights),
            'recommendations': recommendations
        }

        logger.info(f"✅ Generated {len(recommendations)} recommendations for {target_date}")
        return summary

    def store_recommendations(self, target_date: date, recommendations: List[Dict[str, Any]]) -> int:
        """Store recommendations in database."""
        if not recommendations:
            return 0

        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            stored_count = 0

            for rec in recommendations:
                try:
                    cursor.execute("""
                        INSERT INTO daily_trading_recommendations (
                            recommendation_date, symbol, recommendation_type, confidence,
                            astrological_reasoning, supporting_insights, holding_period_days
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (recommendation_date, symbol, recommendation_type) DO UPDATE SET
                            confidence = EXCLUDED.confidence,
                            astrological_reasoning = EXCLUDED.astrological_reasoning,
                            supporting_insights = EXCLUDED.supporting_insights,
                            holding_period_days = EXCLUDED.holding_period_days,
                            created_at = NOW()
                    """, (
                        target_date,
                        rec['symbol'],
                        rec['recommendation_type'],
                        rec['confidence'],
                        rec['astrological_reasoning'],
                        rec['supporting_insights'],
                        rec['holding_period_days']
                    ))
                    stored_count += 1

                except Exception as e:
                    logger.warning(f"⚠️ Failed to store recommendation for {rec['symbol']}: {e}")
                    continue

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"💾 Stored {stored_count}/{len(recommendations)} recommendations")
            return stored_count

        except Exception as e:
            logger.error(f"❌ Database error storing recommendations: {e}")
            return 0

    def get_latest_recommendations(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Get latest recommendations from database."""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT recommendation_date, symbol, recommendation_type, confidence,
                       astrological_reasoning, holding_period_days, created_at
                FROM daily_trading_recommendations
                WHERE recommendation_date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY recommendation_date DESC, confidence DESC
            """, (days_back,))

            recommendations = []
            for row in cursor.fetchall():
                recommendations.append({
                    'recommendation_date': row[0],
                    'symbol': row[1],
                    'recommendation_type': row[2],
                    'confidence': row[3],
                    'astrological_reasoning': row[4],
                    'holding_period_days': row[5],
                    'created_at': row[6]
                })

            cursor.close()
            conn.close()

            return recommendations

        except Exception as e:
            logger.error(f"❌ Error getting latest recommendations: {e}")
            return []