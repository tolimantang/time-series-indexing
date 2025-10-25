#!/usr/bin/env python3
"""
Enhanced Daily Lunar Pattern Tester

Uses PostgreSQL astrological data with daily precision for lunar pattern analysis.
Tests lunar transits with enhanced positional context for next-day price movements.

Architecture:
- Daily lunar positions and aspects from PostgreSQL
- Enhanced positional patterns (target planet signs)
- Daily price data from database
- Store results in lunar_patterns table
"""

import os
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDailyLunarTester:
    def __init__(self, timing_type='next_day'):
        # PostgreSQL connection using environment variables from secrets
        self.conn = psycopg2.connect(
            host=os.environ.get('DB_HOST'),
            database=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            port=os.environ.get('DB_PORT', '5432')
        )

        # Balanced thresholds for daily analysis
        self.ACCURACY_THRESHOLD = 0.65  # 65% accuracy
        self.MIN_OCCURRENCES = 5       # 5 minimum occurrences (higher than hourly)
        self.timing_type = timing_type  # 'same_day' or 'next_day'

    def get_enhanced_planetary_aspects(self, trade_date: datetime) -> List[Dict]:
        """Get all planetary aspects WITH the target planet's sign position"""
        cursor = self.conn.cursor()

        # Get aspects AND the target planet positions
        query = """
        SELECT
            a.planet1,
            a.planet2,
            a.aspect_type,
            a.orb,
            a.separating_angle,
            p.zodiac_sign as target_planet_sign,
            p.degree_in_sign as target_planet_degree
        FROM daily_planetary_aspects a
        JOIN daily_planetary_positions p ON p.planet = a.planet2 AND p.trade_date = a.trade_date
        WHERE a.trade_date = %s
          AND a.planet1 = 'Moon'
          AND a.orb <= 8.0
        ORDER BY a.orb
        """

        cursor.execute(query, (trade_date.date(),))
        results = cursor.fetchall()
        cursor.close()

        aspects = []
        for planet1, planet2, aspect_type, orb, separating_angle, target_sign, target_degree in results:
            aspects.append({
                'planet': planet2,
                'aspect': aspect_type,
                'orb': float(orb),
                'target_sign': target_sign,
                'target_degree': float(target_degree)
            })

        return aspects

    def get_moon_position(self, trade_date: datetime) -> Optional[Dict]:
        """Get Moon position for a specific date"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT longitude, zodiac_sign, degree_in_sign
            FROM daily_planetary_positions
            WHERE planet = 'Moon'
            AND trade_date = %s
        """, (trade_date.date(),))

        result = cursor.fetchone()
        cursor.close()

        if result:
            longitude, zodiac_sign, degree_in_sign = result
            return {
                'longitude': float(longitude),
                'zodiac_sign': zodiac_sign,
                'degree_in_sign': float(degree_in_sign)
            }
        return None

    def get_daily_price_data(self, symbol: str) -> List[Tuple]:
        """Get daily price data from our existing database"""
        logger.info(f"📊 Fetching daily price data from database for {symbol}")

        cursor = self.conn.cursor()

        # Get daily data by getting the last close price of each day
        query = """
        WITH daily_closes AS (
            SELECT
                DATE(datetime) as trade_date,
                close_price,
                ROW_NUMBER() OVER (PARTITION BY DATE(datetime) ORDER BY datetime DESC) as rn
            FROM market_data_intraday
            WHERE symbol = %s
            AND datetime BETWEEN %s AND %s
            AND interval_type = '1h'
        )
        SELECT trade_date, close_price
        FROM daily_closes
        WHERE rn = 1
        ORDER BY trade_date
        """

        start_date = '2023-11-27'
        end_date = '2024-10-24'

        cursor.execute(query, (symbol, start_date, end_date))
        results = cursor.fetchall()
        cursor.close()

        if not results:
            logger.error(f"No price data found in database for {symbol}")
            return []

        # Convert to list of tuples (datetime, close_price)
        price_data = []
        for trade_date, close_price in results:
            # Convert date to datetime for consistency
            dt = datetime.combine(trade_date, datetime.min.time())
            price_data.append((dt, float(close_price)))

        logger.info(f"✅ Successfully retrieved {len(price_data)} daily price points from database")
        return price_data

    def analyze_enhanced_daily_patterns(self, symbol: str) -> List[Dict]:
        """Analyze enhanced daily lunar patterns with precise timing and positional context"""
        logger.info(f"🎯 Analyzing ENHANCED daily lunar patterns for {symbol} ({self.timing_type} movements)")

        # Get daily price data from database
        price_data = self.get_daily_price_data(symbol)

        if not price_data:
            logger.error(f"No daily price data found for {symbol}")
            return []

        logger.info(f"📊 Processing {len(price_data)} daily price points for enhanced {self.timing_type} analysis")
        patterns = {}
        processed_count = 0
        pattern_hits = 0

        # Track date range for analysis_period fields
        start_date = None
        end_date = None

        for i in range(len(price_data) - 1):  # Need next day for next_day analysis
            current_date, current_price = price_data[i]

            # For same_day analysis, we need open price (approximated as previous close)
            if self.timing_type == 'same_day':
                if i == 0:
                    continue  # Skip first day as we need previous price
                prev_date, prev_price = price_data[i - 1]
                reference_price = prev_price  # Use previous close as "open"
                target_price = current_price  # Current close
            else:
                # For next_day analysis
                next_date, next_price = price_data[i + 1]
                reference_price = current_price
                target_price = next_price

            # Track date range
            if start_date is None:
                start_date = current_date
            end_date = current_date

            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() >= 5:
                continue

            # Get Moon position for this date
            lunar_pos = self.get_moon_position(current_date)
            if not lunar_pos:
                continue

            # Get enhanced aspects with target planet signs
            aspects = self.get_enhanced_planetary_aspects(current_date)

            # Calculate price movement based on timing type
            price_change = ((target_price - reference_price) / reference_price) * 100
            direction = 'up' if price_change > 0.1 else 'down' if price_change < -0.1 else 'flat'

            if direction == 'flat':
                continue

            processed_count += 1

            # BASIC PATTERNS
            sign_pattern = f"Moon in {lunar_pos['zodiac_sign']}"
            if sign_pattern not in patterns:
                patterns[sign_pattern] = {
                    'up': 0, 'down': 0, 'up_moves': [], 'down_moves': [],
                    'moon_sign': lunar_pos['zodiac_sign'], 'aspect_type': '',
                    'target_planet': '', 'target_sign': ''
                }
            patterns[sign_pattern][direction] += 1
            if direction == 'up':
                patterns[sign_pattern]['up_moves'].append(price_change)
            else:
                patterns[sign_pattern]['down_moves'].append(price_change)
            pattern_hits += 1

            # ENHANCED POSITIONAL PATTERNS
            for aspect in aspects:
                # Basic aspect pattern
                basic_aspect_pattern = f"Moon {aspect['aspect']} {aspect['planet']}"
                if basic_aspect_pattern not in patterns:
                    patterns[basic_aspect_pattern] = {
                        'up': 0, 'down': 0, 'up_moves': [], 'down_moves': [],
                        'moon_sign': lunar_pos['zodiac_sign'], 'aspect_type': aspect['aspect'],
                        'target_planet': aspect['planet'], 'target_sign': aspect.get('target_sign', '')
                    }
                patterns[basic_aspect_pattern][direction] += 1
                if direction == 'up':
                    patterns[basic_aspect_pattern]['up_moves'].append(price_change)
                else:
                    patterns[basic_aspect_pattern]['down_moves'].append(price_change)
                pattern_hits += 1

                # ENHANCED: Aspect with target planet sign
                enhanced_aspect_pattern = f"Moon {aspect['aspect']} {aspect['planet']} in {aspect['target_sign']}"
                if enhanced_aspect_pattern not in patterns:
                    patterns[enhanced_aspect_pattern] = {
                        'up': 0, 'down': 0, 'up_moves': [], 'down_moves': [],
                        'moon_sign': lunar_pos['zodiac_sign'], 'aspect_type': aspect['aspect'],
                        'target_planet': aspect['planet'], 'target_sign': aspect['target_sign']
                    }
                patterns[enhanced_aspect_pattern][direction] += 1
                if direction == 'up':
                    patterns[enhanced_aspect_pattern]['up_moves'].append(price_change)
                else:
                    patterns[enhanced_aspect_pattern]['down_moves'].append(price_change)
                pattern_hits += 1

                # ENHANCED: Moon sign + aspect + target planet sign
                full_context_pattern = f"Moon in {lunar_pos['zodiac_sign']} {aspect['aspect']} {aspect['planet']} in {aspect['target_sign']}"
                if full_context_pattern not in patterns:
                    patterns[full_context_pattern] = {
                        'up': 0, 'down': 0, 'up_moves': [], 'down_moves': [],
                        'moon_sign': lunar_pos['zodiac_sign'], 'aspect_type': aspect['aspect'],
                        'target_planet': aspect['planet'], 'target_sign': aspect['target_sign']
                    }
                patterns[full_context_pattern][direction] += 1
                if direction == 'up':
                    patterns[full_context_pattern]['up_moves'].append(price_change)
                else:
                    patterns[full_context_pattern]['down_moves'].append(price_change)
                pattern_hits += 1

            # Log progress every 50 processed points
            if processed_count % 50 == 0:
                logger.info(f"📊 Processed {processed_count} daily movements, recorded {pattern_hits} pattern occurrences")

        logger.info(f"📊 Final stats: {processed_count} daily movements, {pattern_hits} pattern occurrences")
        logger.info(f"📋 Raw patterns found: {len(patterns)}")

        # Filter and evaluate patterns
        valid_patterns = []

        for pattern_name, data in patterns.items():
            total = data['up'] + data['down']

            if total >= self.MIN_OCCURRENCES:
                up_accuracy = data['up'] / total
                down_accuracy = data['down'] / total

                # Calculate averages
                avg_up_move = sum(data['up_moves']) / len(data['up_moves']) if data['up_moves'] else 0.0
                avg_down_move = sum(data['down_moves']) / len(data['down_moves']) if data['down_moves'] else 0.0

                if up_accuracy >= self.ACCURACY_THRESHOLD:
                    expected_return = up_accuracy * avg_up_move
                    valid_patterns.append({
                        'pattern': pattern_name,
                        'predicted_direction': 'up',
                        'accuracy': up_accuracy,
                        'occurrences': total,
                        'up_count': data['up'],
                        'down_count': data['down'],
                        'avg_up_move': avg_up_move,
                        'avg_down_move': avg_down_move,
                        'expected_return': expected_return,
                        'moon_sign': data['moon_sign'],
                        'aspect_type': data['aspect_type'],
                        'target_planet': data['target_planet'],
                        'target_sign': data['target_sign'],
                        'analysis_period_start': start_date,
                        'analysis_period_end': end_date
                    })
                elif down_accuracy >= self.ACCURACY_THRESHOLD:
                    expected_return = down_accuracy * abs(avg_down_move)
                    valid_patterns.append({
                        'pattern': pattern_name,
                        'predicted_direction': 'down',
                        'accuracy': down_accuracy,
                        'occurrences': total,
                        'up_count': data['up'],
                        'down_count': data['down'],
                        'avg_up_move': avg_up_move,
                        'avg_down_move': avg_down_move,
                        'expected_return': expected_return,
                        'moon_sign': data['moon_sign'],
                        'aspect_type': data['aspect_type'],
                        'target_planet': data['target_planet'],
                        'target_sign': data['target_sign'],
                        'analysis_period_start': start_date,
                        'analysis_period_end': end_date
                    })

        # Sort by accuracy
        valid_patterns.sort(key=lambda x: x['accuracy'], reverse=True)

        logger.info(f"✨ Found {len(valid_patterns)} valid enhanced daily lunar patterns for {symbol}")

        return valid_patterns

    def store_patterns(self, patterns: List[Dict], symbol: str):
        """Store patterns in lunar_patterns table using new clean schema"""
        logger.info(f"💾 Storing {len(patterns)} enhanced daily patterns for {symbol}")

        cursor = self.conn.cursor()

        for pattern in patterns:
            cursor.execute("""
                INSERT INTO lunar_patterns
                (pattern_name, pattern_type, timing_type, prediction, accuracy_rate,
                 total_occurrences, up_count, down_count, avg_up_move, avg_down_move, expected_return,
                 aspect_type, moon_sign, target_planet, target_sign,
                 analysis_period_start, analysis_period_end, market_symbol, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (pattern_name, market_symbol, timing_type)
                DO UPDATE SET
                    accuracy_rate = EXCLUDED.accuracy_rate,
                    total_occurrences = EXCLUDED.total_occurrences,
                    up_count = EXCLUDED.up_count,
                    down_count = EXCLUDED.down_count,
                    avg_up_move = EXCLUDED.avg_up_move,
                    avg_down_move = EXCLUDED.avg_down_move,
                    expected_return = EXCLUDED.expected_return,
                    aspect_type = EXCLUDED.aspect_type,
                    moon_sign = EXCLUDED.moon_sign,
                    target_planet = EXCLUDED.target_planet,
                    target_sign = EXCLUDED.target_sign,
                    analysis_period_start = EXCLUDED.analysis_period_start,
                    analysis_period_end = EXCLUDED.analysis_period_end,
                    updated_at = NOW()
            """, (
                pattern['pattern'],
                'lunar_transit',  # Clean pattern type
                self.timing_type,  # Use instance timing type
                pattern['predicted_direction'],
                round(pattern['accuracy'], 3),
                pattern['occurrences'],
                pattern['up_count'],
                pattern['down_count'],
                round(pattern['avg_up_move'], 4),
                round(pattern['avg_down_move'], 4),
                round(pattern['expected_return'], 4),
                pattern['aspect_type'] or None,
                pattern['moon_sign'] or None,
                pattern['target_planet'] or None,
                pattern['target_sign'] or None,
                pattern['analysis_period_start'].date() if pattern['analysis_period_start'] else None,
                pattern['analysis_period_end'].date() if pattern['analysis_period_end'] else None,
                symbol,
                datetime.now()
            ))

        self.conn.commit()
        cursor.close()
        logger.info(f"✅ Successfully stored {len(patterns)} enhanced daily patterns")

    def run_analysis(self, symbol: str, market_name: str):
        """Run the complete enhanced daily lunar analysis"""
        logger.info(f"🚀 Starting ENHANCED Daily Lunar Backtesting Analysis for {market_name}")

        try:
            # Analyze futures with enhanced positional patterns
            patterns = self.analyze_enhanced_daily_patterns(symbol)

            if patterns:
                # Store results
                self.store_patterns(patterns, f"{market_name}_DAILY")

                # Display top patterns
                logger.info(f"🏆 Top Enhanced Daily Lunar Patterns for {market_name}:")
                for i, pattern in enumerate(patterns[:20], 1):
                    logger.info(f"{i:2d}. {pattern['pattern']:<60} → {pattern['predicted_direction']:<4} "
                              f"({pattern['accuracy']:.1%} accuracy, {pattern['occurrences']:2d} occurrences)")

                logger.info(f"\n📈 Summary: Found {len(patterns)} predictive enhanced daily patterns with ≥{self.ACCURACY_THRESHOLD:.0%} accuracy")
            else:
                logger.warning("No significant enhanced daily lunar patterns found")

            logger.info(f"🎯 Enhanced daily lunar analysis completed successfully for {market_name}!")

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()

def main():
    """Main execution"""
    import sys

    if len(sys.argv) not in [3, 4]:
        print("Usage: python enhanced_daily_lunar_tester.py <SYMBOL> <MARKET_NAME> [TIMING_TYPE]")
        print("Example: python enhanced_daily_lunar_tester.py PLATINUM_FUTURES PLATINUM next_day")
        print("TIMING_TYPE: 'same_day' or 'next_day' (default: next_day)")
        sys.exit(1)

    symbol = sys.argv[1]
    market_name = sys.argv[2]
    timing_type = sys.argv[3] if len(sys.argv) == 4 else 'next_day'

    if timing_type not in ['same_day', 'next_day']:
        print("Error: TIMING_TYPE must be 'same_day' or 'next_day'")
        sys.exit(1)

    tester = EnhancedDailyLunarTester(timing_type=timing_type)
    tester.run_analysis(symbol, market_name)

if __name__ == "__main__":
    main()