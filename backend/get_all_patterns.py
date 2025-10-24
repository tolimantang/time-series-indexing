#!/usr/bin/env python3
"""
Get all 5 lunar patterns from the database directly
"""

import psycopg2
import os
from datetime import datetime, timedelta

# Database configuration from environment
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'financial_postgres'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

def get_all_patterns():
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Same query as the job used
    query = """
    WITH lunar_events AS (
        SELECT DISTINCT
            dc.trade_date as event_date,
            CONCAT(pa.aspect_type, ' ', pa.planet2) as pattern
        FROM daily_astrological_conditions dc
        JOIN daily_planetary_aspects pa ON dc.id = pa.conditions_id
        WHERE pa.planet1 = 'Moon'
          AND dc.trade_date >= CURRENT_DATE - INTERVAL '5 years'
          AND pa.orb <= 3.0
    ),
    price_movements AS (
        SELECT
            le.pattern,
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
          AND p1.close_price != p2.close_price  -- Exclude no-change days
    )
    SELECT
        pattern,
        direction,
        COUNT(*) as count,
        AVG(pct_change) as avg_change
    FROM price_movements
    GROUP BY pattern, direction
    HAVING COUNT(*) >= 3  -- Minimum 3 occurrences
    ORDER BY pattern, direction
    """

    cursor.execute(query)
    results = cursor.fetchall()

    # Process results into patterns
    patterns = {}
    for pattern, direction, count, avg_change in results:
        if pattern not in patterns:
            patterns[pattern] = {'up': 0, 'down': 0, 'up_avg': 0, 'down_avg': 0}

        patterns[pattern][direction] = count
        patterns[pattern][f"{direction}_avg"] = float(avg_change)

    # Find predictive patterns (>65% accuracy)
    predictive = []
    for pattern, data in patterns.items():
        total = data['up'] + data['down']
        if total >= 5:  # Need at least 5 total occurrences
            up_rate = data['up'] / total
            down_rate = data['down'] / total

            if up_rate >= 0.65:
                predictive.append({
                    'pattern': f"Moon {pattern}",
                    'prediction': 'BULLISH',
                    'accuracy': up_rate,
                    'occurrences': total,
                    'up_count': data['up'],
                    'down_count': data['down'],
                    'avg_up_move': data['up_avg'],
                    'avg_down_move': data['down_avg']
                })
            elif down_rate >= 0.65:
                predictive.append({
                    'pattern': f"Moon {pattern}",
                    'prediction': 'BEARISH',
                    'accuracy': down_rate,
                    'occurrences': total,
                    'up_count': data['up'],
                    'down_count': data['down'],
                    'avg_up_move': data['up_avg'],
                    'avg_down_move': data['down_avg']
                })

    # Sort by accuracy
    predictive.sort(key=lambda x: x['accuracy'], reverse=True)

    print(f"\n🌙 ALL 5 LUNAR PATTERNS FOUND:")
    print("=" * 50)

    for i, p in enumerate(predictive, 1):
        direction_emoji = "📈" if p['prediction'] == 'BULLISH' else "📉"
        print(f"{i}. {p['pattern']} → {p['prediction']} {direction_emoji}")
        print(f"   Accuracy: {p['accuracy']:.1%}")
        print(f"   Sample: {p['occurrences']} events (↑{p['up_count']} ↓{p['down_count']})")

        if p['prediction'] == 'BULLISH':
            print(f"   Avg Up Move: +{p['avg_up_move']:.2f}%")
            expected = p['accuracy'] * p['avg_up_move']
            print(f"   Expected Return: +{expected:.2f}% per signal")
        else:
            print(f"   Avg Down Move: {p['avg_down_move']:.2f}%")
            expected = p['accuracy'] * abs(p['avg_down_move'])
            print(f"   Expected Return: +{expected:.2f}% (short)")
        print()

    cursor.close()
    conn.close()

    return predictive

if __name__ == "__main__":
    patterns = get_all_patterns()
    print(f"Total patterns found: {len(patterns)}")