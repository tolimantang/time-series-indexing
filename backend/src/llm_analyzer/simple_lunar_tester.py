#!/usr/bin/env python3
"""
Simple Next-Day Lunar Pattern Tester

Tests the simple hypothesis: Does a lunar transit predict next-day oil price movement?
- Day 0: Moon aspect occurs
- Day +1: Oil price direction (up/down vs Day 0)

Since Moon moves ~13 degrees/day, one day captures the immediate transit effect.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psycopg2

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleLunarTester:
    """Simple lunar tester: lunar event → next day price movement"""

    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None

    def connect_db(self):
        self.conn = psycopg2.connect(**self.db_config)
        logger.info("Connected to database")

    def get_lunar_events_and_prices(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get lunar events with next-day price movements"""
        cursor = self.conn.cursor()

        # Simple query: lunar events + next-day price change
        query = """
        WITH lunar_events AS (
            SELECT DISTINCT
                dc.trade_date as event_date,
                pa.aspect_type,
                pa.planet2 as target_planet,
                pa.orb
            FROM daily_astrological_conditions dc
            JOIN daily_planetary_aspects pa ON dc.id = pa.conditions_id
            WHERE pa.planet1 = 'Moon'
              AND dc.trade_date BETWEEN %s AND %s
              AND pa.orb <= 3.0
        ),
        price_changes AS (
            SELECT
                event_date,
                aspect_type,
                target_planet,
                orb,
                p1.close_price as day0_price,
                p2.close_price as day1_price,
                CASE
                    WHEN p2.close_price > p1.close_price THEN 'up'
                    WHEN p2.close_price < p1.close_price THEN 'down'
                    ELSE 'same'
                END as direction,
                ((p2.close_price - p1.close_price) / p1.close_price) * 100 as pct_change
            FROM lunar_events le
            JOIN market_data p1 ON p1.trade_date = le.event_date
                AND p1.symbol = 'CRUDE_OIL_WTI'
            JOIN market_data p2 ON p2.trade_date = le.event_date + INTERVAL '1 day'
                AND p2.symbol = 'CRUDE_OIL_WTI'
            WHERE p1.close_price IS NOT NULL
              AND p2.close_price IS NOT NULL
        )
        SELECT
            event_date,
            aspect_type,
            target_planet,
            orb,
            day0_price,
            day1_price,
            direction,
            pct_change
        FROM price_changes
        ORDER BY event_date
        """

        cursor.execute(query, (start_date.date(), end_date.date()))
        results = cursor.fetchall()

        events = []
        for row in results:
            events.append({
                'event_date': row[0],
                'aspect_type': row[1],
                'target_planet': row[2],
                'orb': float(row[3]),
                'day0_price': float(row[4]),
                'day1_price': float(row[5]),
                'direction': row[6],
                'pct_change': float(row[7])
            })

        cursor.close()
        logger.info(f"Found {len(events)} lunar events with next-day price data")
        return events

    def analyze_patterns(self, events: List[Dict]) -> Dict[str, Any]:
        """Analyze lunar patterns for next-day price prediction"""
        patterns = {}

        # Group by aspect type and planet
        for event in events:
            if event['direction'] == 'same':  # Skip no-change days
                continue

            key = f"Moon {event['aspect_type']} {event['target_planet']}"
            if key not in patterns:
                patterns[key] = {'up': 0, 'down': 0, 'changes': []}

            patterns[key][event['direction']] += 1
            patterns[key]['changes'].append(event['pct_change'])

        # Calculate success rates
        results = []
        for pattern_name, data in patterns.items():
            total = data['up'] + data['down']
            if total < 3:  # Need at least 3 occurrences
                continue

            up_rate = data['up'] / total
            down_rate = data['down'] / total

            # Determine if pattern is bullish or bearish
            if up_rate > 0.65:  # 65% threshold
                result = {
                    'pattern': pattern_name,
                    'prediction': 'bullish',
                    'success_rate': up_rate,
                    'occurrences': total,
                    'up_count': data['up'],
                    'down_count': data['down'],
                    'avg_change': sum(data['changes']) / len(data['changes']),
                    'avg_up_change': sum([c for c in data['changes'] if c > 0]) / len([c for c in data['changes'] if c > 0]) if any(c > 0 for c in data['changes']) else 0,
                    'avg_down_change': sum([c for c in data['changes'] if c < 0]) / len([c for c in data['changes'] if c < 0]) if any(c < 0 for c in data['changes']) else 0
                }
                results.append(result)
            elif down_rate > 0.65:
                result = {
                    'pattern': pattern_name,
                    'prediction': 'bearish',
                    'success_rate': down_rate,
                    'occurrences': total,
                    'up_count': data['up'],
                    'down_count': data['down'],
                    'avg_change': sum(data['changes']) / len(data['changes']),
                    'avg_up_change': sum([c for c in data['changes'] if c > 0]) / len([c for c in data['changes'] if c > 0]) if any(c > 0 for c in data['changes']) else 0,
                    'avg_down_change': sum([c for c in data['changes'] if c < 0]) / len([c for c in data['changes'] if c < 0]) if any(c < 0 for c in data['changes']) else 0
                }
                results.append(result)

        # Sort by success rate
        results.sort(key=lambda x: x['success_rate'], reverse=True)
        return results

    def run_analysis(self, start_date: datetime, end_date: datetime):
        """Run the complete next-day lunar analysis"""
        self.connect_db()

        try:
            # Get events with next-day price changes
            events = self.get_lunar_events_and_prices(start_date, end_date)

            if not events:
                print("❌ No lunar events with price data found")
                return {'success': False, 'error': 'No data'}

            # Analyze patterns
            patterns = self.analyze_patterns(events)

            # Print results
            print(f"\n🌙 SIMPLE NEXT-DAY LUNAR ANALYSIS")
            print(f"=" * 50)
            print(f"Period: {start_date.date()} to {end_date.date()}")
            print(f"Total lunar events with price data: {len(events)}")
            print(f"Significant patterns found: {len(patterns)}")

            if patterns:
                print(f"\n📈 NEXT-DAY PREDICTION PATTERNS:")
                print("-" * 40)

                for i, pattern in enumerate(patterns, 1):
                    direction_emoji = "📈" if pattern['prediction'] == 'bullish' else "📉"
                    print(f"{i}. {pattern['pattern']} → {pattern['prediction']} {direction_emoji}")
                    print(f"   Success Rate: {pattern['success_rate']:.1%}")
                    print(f"   Occurrences: {pattern['occurrences']} (↑{pattern['up_count']} ↓{pattern['down_count']})")
                    print(f"   Avg Change: {pattern['avg_change']:.2f}%")
                    if pattern['prediction'] == 'bullish':
                        print(f"   Avg Up Move: {pattern['avg_up_change']:.2f}%")
                    else:
                        print(f"   Avg Down Move: {pattern['avg_down_change']:.2f}%")
                    print()

                # Trading summary
                print(f"📊 TRADING INSIGHTS:")
                print("-" * 20)
                best_pattern = patterns[0]
                print(f"Best Pattern: {best_pattern['pattern']}")
                print(f"Prediction: {best_pattern['prediction']} with {best_pattern['success_rate']:.1%} accuracy")

                if best_pattern['prediction'] == 'bullish':
                    expected_return = best_pattern['success_rate'] * best_pattern['avg_up_change']
                    print(f"Expected Return: +{expected_return:.2f}% per signal")
                else:
                    expected_return = best_pattern['success_rate'] * abs(best_pattern['avg_down_change'])
                    print(f"Expected Return: -{expected_return:.2f}% per signal (short)")

                # Signal frequency
                total_days = (end_date - start_date).days
                signals_per_year = (len(events) / total_days) * 365
                print(f"Signal Frequency: {signals_per_year:.1f} lunar events per year")

            else:
                print("❌ No significant next-day patterns found")
                print("Lunar transits may not predict next-day oil movements")

            return {
                'success': len(patterns) > 0,
                'patterns': patterns,
                'total_events': len(events)
            }

        finally:
            if self.conn:
                self.conn.close()

def main():
    """Main execution"""
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'financial_postgres'),
        'port': int(os.getenv('DB_PORT', '5432'))
    }

    print("🚀 Starting Simple Next-Day Lunar Analysis")
    print("Testing: Lunar Transit → Next Day Oil Price Movement")

    # Test period: last 5 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)

    print(f"📅 Period: {start_date.date()} to {end_date.date()}")
    print("🛢️ Using real WTI crude oil prices")
    print("📈 Measuring next-day price direction only")

    tester = SimpleLunarTester(db_config)
    results = tester.run_analysis(start_date, end_date)

    if results['success']:
        print(f"\n✅ Found predictive lunar patterns!")
        print(f"Some lunar transits DO predict next-day oil movements")
    else:
        print(f"\n⚠️ No predictive patterns found")
        print(f"Lunar transits may not affect next-day oil prices")

    return results

if __name__ == "__main__":
    main()