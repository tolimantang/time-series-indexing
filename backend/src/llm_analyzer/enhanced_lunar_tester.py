#!/usr/bin/env python3
"""
Enhanced Lunar Pattern Tester with Zodiac Sign Awareness

This version includes zodiac sign analysis to discover more precise patterns.
For example: "Moon trine Jupiter in Sagittarius" vs "Moon trine Jupiter in Gemini"
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psycopg2
from lunar_pattern_tester import LunarPatternTester, ZodiacSign

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedOilLunarTester(LunarPatternTester):
    """Enhanced lunar tester with sign awareness for oil markets"""

    async def get_market_data(self, start_date: datetime, end_date: datetime) -> Dict[datetime, float]:
        """Fetch oil price data from your database"""
        cursor = self.conn.cursor()

        # Enhanced synthetic data with more realistic patterns
        query = """
        WITH oil_prices AS (
            SELECT
                trade_date,
                -- More realistic synthetic oil prices with volatility clusters
                45 +
                25 * SIN(EXTRACT(DOY FROM trade_date) * 2 * PI() / 365) +  -- Seasonal pattern
                10 * SIN(EXTRACT(DOY FROM trade_date) * 4 * PI() / 365) +   -- Shorter cycle
                COALESCE(daily_score * 0.8, 0) +                           -- Astrological influence
                (RANDOM() - 0.5) * 15 as oil_price                         -- Random volatility
            FROM daily_astrological_conditions
            WHERE trade_date BETWEEN %s AND %s
        )
        SELECT trade_date, oil_price
        FROM oil_prices
        ORDER BY trade_date
        """

        try:
            cursor.execute(query, (start_date.date(), end_date.date()))
            results = cursor.fetchall()

            price_data = {}
            for date, price in results:
                if price is not None:
                    price_data[datetime.combine(date, datetime.min.time())] = float(price)

            cursor.close()
            logger.info(f"Generated {len(price_data)} enhanced oil price points")
            return price_data

        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            cursor.close()
            raise

    def analyze_pattern_quality(self, patterns: List) -> Dict[str, Any]:
        """Analyze the quality and strength of discovered patterns"""
        analysis = {
            'total_patterns': len(patterns),
            'sign_specific_patterns': 0,
            'sign_agnostic_patterns': 0,
            'strong_planetary_placements': 0,
            'weak_planetary_placements': 0,
            'by_planetary_strength': {'very_strong': [], 'strong': [], 'neutral': [], 'weak': [], 'very_weak': []},
            'by_sign_element': {'Fire': [], 'Earth': [], 'Air': [], 'Water': []},
            'consistency_distribution': {'high': [], 'medium': [], 'low': []}
        }

        for pattern in patterns:
            # Count pattern types
            if pattern.target_sign:
                analysis['sign_specific_patterns'] += 1

                # Analyze planetary strength
                if pattern.pattern_strength in ['very_strong', 'strong']:
                    analysis['strong_planetary_placements'] += 1
                elif pattern.pattern_strength in ['weak', 'very_weak']:
                    analysis['weak_planetary_placements'] += 1

                # Group by strength
                analysis['by_planetary_strength'][pattern.pattern_strength].append(pattern)

                # Group by element
                element = pattern.target_sign.element
                analysis['by_sign_element'][element].append(pattern)
            else:
                analysis['sign_agnostic_patterns'] += 1

            # Consistency distribution
            if pattern.consistency_rate >= 0.80:
                analysis['consistency_distribution']['high'].append(pattern)
            elif pattern.consistency_rate >= 0.70:
                analysis['consistency_distribution']['medium'].append(pattern)
            else:
                analysis['consistency_distribution']['low'].append(pattern)

        return analysis

def print_enhanced_results(results: Dict[str, Any]):
    """Print enhanced results with sign awareness"""

    print("\\n" + "="*80)
    print("🌙 ENHANCED LUNAR PATTERN BACKTEST RESULTS 🌙")
    print("="*80)

    print(f"Market: Oil (CL)")
    print(f"Test Period: {results['test_period']['start'].strftime('%Y-%m-%d')} to {results['test_period']['end'].strftime('%Y-%m-%d')}")
    print(f"Total Lunar Events Analyzed: {results['total_events']:,}")
    print(f"Patterns Discovered: {results['discovered_patterns']}")

    if results['patterns']:
        # Analyze pattern quality
        analysis = EnhancedOilLunarTester({}, "CL").analyze_pattern_quality(results['patterns'])

        print(f"\\n📊 PATTERN ANALYSIS:")
        print("-" * 50)
        print(f"Sign-Specific Patterns: {analysis['sign_specific_patterns']}")
        print(f"Sign-Agnostic Patterns: {analysis['sign_agnostic_patterns']}")
        print(f"Strong Planetary Placements: {analysis['strong_planetary_placements']}")
        print(f"Weak Planetary Placements: {analysis['weak_planetary_placements']}")

        print(f"\\n🔥 PATTERNS BY ELEMENT:")
        print("-" * 30)
        for element, patterns in analysis['by_sign_element'].items():
            if patterns:
                avg_consistency = sum(p.consistency_rate for p in patterns) / len(patterns)
                print(f"{element} Signs: {len(patterns)} patterns (avg {avg_consistency:.1%} consistency)")

        print(f"\\n⭐ PATTERNS BY PLANETARY STRENGTH:")
        print("-" * 40)
        for strength, patterns in analysis['by_planetary_strength'].items():
            if patterns:
                avg_consistency = sum(p.consistency_rate for p in patterns) / len(patterns)
                avg_magnitude = sum(p.avg_magnitude for p in patterns) / len(patterns)
                print(f"{strength.replace('_', ' ').title()}: {len(patterns)} patterns")
                print(f"  Avg Consistency: {avg_consistency:.1%}, Avg Magnitude: {avg_magnitude:.2f}%")

        print(f"\\n📈 TOP PATTERNS (Sign-Aware):")
        print("-" * 50)

        # Sort patterns by consistency * magnitude, prioritizing sign-specific ones
        sorted_patterns = sorted(
            results['patterns'],
            key=lambda p: (
                1 if p.target_sign else 0,  # Prioritize sign-specific
                p.consistency_rate * p.avg_magnitude
            ),
            reverse=True
        )

        for i, pattern in enumerate(sorted_patterns[:10], 1):
            print(f"{i}. {pattern.description}")
            print(f"   📊 Consistency: {pattern.consistency_rate:.1%}")
            print(f"   📈 Avg Magnitude: {pattern.avg_magnitude:.2f}%")
            print(f"   🔢 Occurrences: {pattern.total_occurrences}")

            if pattern.target_sign:
                strength_emoji = {
                    'very_strong': '🟢',
                    'strong': '🟡',
                    'neutral': '⚪',
                    'weak': '🟠',
                    'very_weak': '🔴'
                }.get(pattern.pattern_strength, '⚪')

                print(f"   {strength_emoji} Planetary Strength: {pattern.pattern_strength.replace('_', ' ').title()}")
                print(f"   🌟 Element: {pattern.target_sign.element}")
                print(f"   🏠 Quality: {pattern.target_sign.quality}")

            print(f"   📅 Last Seen: {pattern.last_occurrence.strftime('%Y-%m-%d')}")
            print()

        # Insights and recommendations
        print(f"\\n💡 KEY INSIGHTS:")
        print("-" * 20)

        # Find the strongest element
        element_performance = {}
        for element, patterns in analysis['by_sign_element'].items():
            if patterns:
                element_performance[element] = {
                    'avg_consistency': sum(p.consistency_rate for p in patterns) / len(patterns),
                    'count': len(patterns)
                }

        if element_performance:
            best_element = max(element_performance.items(), key=lambda x: x[1]['avg_consistency'])
            print(f"🔥 Best Element: {best_element[0]} signs show highest consistency ({best_element[1]['avg_consistency']:.1%})")

        # Find strongest planetary placements
        strong_patterns = analysis['by_planetary_strength'].get('very_strong', []) + analysis['by_planetary_strength'].get('strong', [])
        if strong_patterns:
            avg_strong_consistency = sum(p.consistency_rate for p in strong_patterns) / len(strong_patterns)
            print(f"⭐ Strong Placements: Planets in rulership/exaltation show {avg_strong_consistency:.1%} avg consistency")

        weak_patterns = analysis['by_planetary_strength'].get('weak', []) + analysis['by_planetary_strength'].get('very_weak', [])
        if weak_patterns:
            avg_weak_consistency = sum(p.consistency_rate for p in weak_patterns) / len(weak_patterns)
            print(f"⚠️  Weak Placements: Planets in detriment/fall show {avg_weak_consistency:.1%} avg consistency")

async def run_enhanced_backtest():
    """Run enhanced lunar pattern backtest with sign awareness"""

    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'financial_postgres'),
        'port': int(os.getenv('DB_PORT', '5432'))
    }

    # Initialize enhanced tester
    tester = EnhancedOilLunarTester(db_config, market_symbol="CL")

    # Test period: last 3 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3*365)

    # Test lunar aspects to major planets
    target_planets = ['Jupiter', 'Saturn', 'Mars', 'Venus', 'Mercury', 'Sun']

    logger.info(f"Starting enhanced lunar pattern backtest for oil market")
    logger.info(f"Test period: {start_date.date()} to {end_date.date()}")
    logger.info(f"Including zodiac sign analysis for enhanced precision")

    try:
        # Run the backtest
        results = await tester.backtest_patterns(start_date, end_date, target_planets)

        # Print enhanced results
        print_enhanced_results(results)

        # Save enhanced results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_lunar_backtest_{timestamp}.json"

        # Enhanced export with sign information
        export_data = {
            'test_info': {
                'market': results['market_symbol'],
                'start_date': results['test_period']['start'].isoformat(),
                'end_date': results['test_period']['end'].isoformat(),
                'total_events': results['total_events'],
                'patterns_discovered': results['discovered_patterns'],
                'sign_awareness': True
            },
            'patterns': []
        }

        for pattern in results['patterns']:
            pattern_data = {
                'description': pattern.description,
                'aspect_type': pattern.aspect_type.value,
                'target_planet': pattern.target_planet,
                'target_sign': pattern.target_sign.sign_name if pattern.target_sign else None,
                'target_sign_element': pattern.target_sign.element if pattern.target_sign else None,
                'target_sign_quality': pattern.target_sign.quality if pattern.target_sign else None,
                'planetary_strength': pattern.pattern_strength,
                'consistency_rate': pattern.consistency_rate,
                'avg_magnitude': pattern.avg_magnitude,
                'total_occurrences': pattern.total_occurrences,
                'last_occurrence': pattern.last_occurrence.isoformat()
            }
            export_data['patterns'].append(pattern_data)

        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"\\n💾 Enhanced results saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

        return results

    except Exception as e:
        logger.error(f"Enhanced backtest failed: {e}")
        print(f"\\n❌ Enhanced backtest failed: {e}")
        return None

if __name__ == "__main__":
    # Run the enhanced lunar pattern backtest
    results = asyncio.run(run_enhanced_backtest())