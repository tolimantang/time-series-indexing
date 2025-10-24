#!/usr/bin/env python3
"""
Real Oil Price Lunar Pattern Tester

This version uses actual WTI crude oil price data from the market_data table
instead of synthetic data, providing realistic backtesting results.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psycopg2
from lunar_pattern_tester import LunarPatternTester, LunarAspectType, ZodiacSign

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealOilLunarTester(LunarPatternTester):
    """Lunar tester using real WTI crude oil price data"""

    async def get_market_data(self, start_date: datetime, end_date: datetime) -> Dict[datetime, float]:
        """Fetch real WTI crude oil price data from market_data table"""
        cursor = self.conn.cursor()

        # Query real WTI oil price data
        query = """
        SELECT trade_date, close_price
        FROM market_data
        WHERE symbol = 'CRUDE_OIL_WTI'
          AND trade_date BETWEEN %s AND %s
          AND close_price IS NOT NULL
        ORDER BY trade_date
        """

        try:
            cursor.execute(query, (start_date.date(), end_date.date()))
            results = cursor.fetchall()

            if not results:
                logger.warning(f"No WTI oil price data found between {start_date.date()} and {end_date.date()}")
                cursor.close()
                return {}

            price_data = {}
            for date, price in results:
                if price is not None:
                    price_data[datetime.combine(date, datetime.min.time())] = float(price)

            cursor.close()
            logger.info(f"Loaded {len(price_data)} real WTI oil price points from {min(price_data.keys()).date()} to {max(price_data.keys()).date()}")

            # Log price range for context
            prices = list(price_data.values())
            logger.info(f"Price range: ${min(prices):.2f} - ${max(prices):.2f} per barrel")

            return price_data

        except Exception as e:
            logger.error(f"Error fetching real oil price data: {e}")
            cursor.close()
            raise

    async def validate_data_availability(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Check data availability for the requested period"""
        cursor = self.conn.cursor()

        # Check oil price data availability
        oil_query = """
        SELECT
            MIN(trade_date) as earliest_date,
            MAX(trade_date) as latest_date,
            COUNT(*) as total_records,
            COUNT(DISTINCT trade_date) as unique_dates
        FROM market_data
        WHERE symbol = 'CRUDE_OIL_WTI'
          AND close_price IS NOT NULL
        """

        # Check astrological data availability
        astro_query = """
        SELECT
            MIN(trade_date) as earliest_date,
            MAX(trade_date) as latest_date,
            COUNT(*) as total_records
        FROM daily_astrological_conditions
        WHERE trade_date BETWEEN %s AND %s
        """

        try:
            cursor.execute(oil_query)
            oil_result = cursor.fetchone()

            cursor.execute(astro_query, (start_date.date(), end_date.date()))
            astro_result = cursor.fetchone()

            cursor.close()

            validation = {
                'oil_data': {
                    'earliest_date': oil_result[0],
                    'latest_date': oil_result[1],
                    'total_records': oil_result[2],
                    'unique_dates': oil_result[3]
                },
                'astro_data': {
                    'earliest_date': astro_result[0],
                    'latest_date': astro_result[1],
                    'total_records': astro_result[2]
                },
                'requested_period': {
                    'start_date': start_date.date(),
                    'end_date': end_date.date()
                }
            }

            # Determine optimal test period
            oil_start = oil_result[0] if oil_result[0] else start_date.date()
            oil_end = oil_result[1] if oil_result[1] else end_date.date()
            astro_start = astro_result[0] if astro_result[0] else start_date.date()
            astro_end = astro_result[1] if astro_result[1] else end_date.date()

            # Find overlap
            optimal_start = max(oil_start, astro_start, start_date.date())
            optimal_end = min(oil_end, astro_end, end_date.date())

            validation['optimal_period'] = {
                'start_date': optimal_start,
                'end_date': optimal_end,
                'duration_days': (optimal_end - optimal_start).days
            }

            return validation

        except Exception as e:
            logger.error(f"Error validating data availability: {e}")
            cursor.close()
            raise

def print_real_oil_results(results: Dict[str, Any], validation: Dict[str, Any]):
    """Print results with real oil price context"""

    print("\\n" + "="*80)
    print("🛢️  REAL WTI OIL PRICE LUNAR PATTERN BACKTEST 🛢️")
    print("="*80)

    print(f"Market: WTI Crude Oil (Real Price Data)")
    print(f"Test Period: {results['test_period']['start'].strftime('%Y-%m-%d')} to {results['test_period']['end'].strftime('%Y-%m-%d')}")
    print(f"Duration: {(results['test_period']['end'] - results['test_period']['start']).days:,} days")

    # Data context
    oil_data = validation['oil_data']
    print(f"\\n📊 DATA OVERVIEW:")
    print("-" * 30)
    print(f"WTI Price Data: {oil_data['earliest_date']} to {oil_data['latest_date']} ({oil_data['unique_dates']:,} trading days)")
    print(f"Astrological Data: {validation['astro_data']['total_records']:,} daily records")
    print(f"Total Lunar Events Analyzed: {results['total_events']:,}")

    if results['patterns']:
        print(f"\\n🌙 DISCOVERED PATTERNS ({len(results['patterns'])} total):")
        print("-" * 50)

        # Sort patterns by consistency * magnitude (most profitable first)
        sorted_patterns = sorted(
            results['patterns'],
            key=lambda p: p.consistency_rate * p.avg_magnitude,
            reverse=True
        )

        for i, pattern in enumerate(sorted_patterns, 1):
            print(f"{i}. {pattern.description}")
            print(f"   📊 Consistency: {pattern.consistency_rate:.1%} ({pattern.total_occurrences} occurrences)")
            print(f"   💰 Avg Move: {pattern.avg_magnitude:.2f}% per move")
            print(f"   📈 Potential Annual Impact: ~{pattern.avg_magnitude * (pattern.total_occurrences / ((results['test_period']['end'] - results['test_period']['start']).days / 365)):.1f}%")
            print(f"   ⏱️  Avg Duration: {pattern.avg_duration:.1f} days")
            print(f"   📅 Last Seen: {pattern.last_occurrence.strftime('%Y-%m-%d')}")

            # Add sign information if available
            if hasattr(pattern, 'target_sign') and pattern.target_sign:
                print(f"   🌟 Planet in {pattern.target_sign.sign_name} ({pattern.target_sign.element} sign)")
                if hasattr(pattern, 'pattern_strength'):
                    strength_emoji = {
                        'very_strong': '🟢', 'strong': '🟡', 'neutral': '⚪',
                        'weak': '🟠', 'very_weak': '🔴'
                    }.get(pattern.pattern_strength, '⚪')
                    print(f"   {strength_emoji} Planetary Strength: {pattern.pattern_strength.replace('_', ' ').title()}")
            print()

        # Trading insights
        print(f"\\n💡 TRADING INSIGHTS:")
        print("-" * 25)

        # Best patterns for trading
        high_consistency = [p for p in sorted_patterns if p.consistency_rate >= 0.75]
        if high_consistency:
            best_pattern = high_consistency[0]
            print(f"🎯 Highest Confidence Pattern: {best_pattern.description}")
            print(f"   Success Rate: {best_pattern.consistency_rate:.1%}")
            print(f"   Average Move: {best_pattern.avg_magnitude:.2f}%")

            # Calculate expected value
            expected_value = best_pattern.consistency_rate * best_pattern.avg_magnitude
            print(f"   Expected Value: +{expected_value:.2f}% per signal")

        # Frequency analysis
        total_days = (results['test_period']['end'] - results['test_period']['start']).days
        total_signals = sum(p.total_occurrences for p in results['patterns'])
        avg_signals_per_year = (total_signals / total_days) * 365

        print(f"\\n📈 FREQUENCY ANALYSIS:")
        print(f"   Total Signals: {total_signals} over {total_days:,} days")
        print(f"   Average Signals/Year: {avg_signals_per_year:.1f}")
        print(f"   Signal Frequency: Every {total_days/total_signals:.0f} days on average")

        # Risk assessment
        max_drawdown_pattern = min(sorted_patterns, key=lambda p: p.avg_magnitude)
        print(f"\\n⚠️  RISK ASSESSMENT:")
        print(f"   Largest Average Move: {max(p.avg_magnitude for p in sorted_patterns):.2f}%")
        print(f"   Smallest Average Move: {min(p.avg_magnitude for p in sorted_patterns):.2f}%")
        print(f"   Pattern with Lowest Magnitude: {max_drawdown_pattern.description} ({max_drawdown_pattern.avg_magnitude:.2f}%)")

    else:
        print("\\n❌ No significant patterns discovered in real oil price data")
        print("This could indicate:")
        print("- Lunar patterns may not have strong predictive power for oil")
        print("- Different parameters or longer time periods may be needed")
        print("- Market efficiency may have eliminated astrological patterns")

async def run_real_oil_backtest(test_period: str = 'comprehensive') -> Dict[str, Any]:
    """Run comprehensive lunar pattern backtest on real WTI oil prices"""

    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'financial_postgres'),
        'port': int(os.getenv('DB_PORT', '5432'))
    }

    # Initialize real oil price tester
    tester = RealOilLunarTester(db_config, market_symbol="CRUDE_OIL_WTI")

    # Define test periods
    test_periods = {
        'recent': {
            'start': datetime.now() - timedelta(days=2*365),  # 2 years
            'end': datetime.now()
        },
        'medium': {
            'start': datetime.now() - timedelta(days=5*365),  # 5 years
            'end': datetime.now()
        },
        'long': {
            'start': datetime.now() - timedelta(days=10*365),  # 10 years
            'end': datetime.now()
        },
        'comprehensive': {
            'start': datetime.now() - timedelta(days=20*365),  # 20 years
            'end': datetime.now()
        }
    }

    period = test_periods[test_period]
    start_date = period['start']
    end_date = period['end']

    logger.info(f"Starting real WTI oil price lunar pattern backtest")
    logger.info(f"Requested period: {start_date.date()} to {end_date.date()}")

    try:
        # Connect and validate data availability
        await tester.connect_db()
        validation = await tester.validate_data_availability(start_date, end_date)

        # Use optimal period based on data availability
        optimal_start = datetime.combine(validation['optimal_period']['start_date'], datetime.min.time())
        optimal_end = datetime.combine(validation['optimal_period']['end_date'], datetime.min.time())

        if optimal_start >= optimal_end:
            raise ValueError("No overlapping data found between oil prices and astrological data")

        logger.info(f"Using optimal period: {optimal_start.date()} to {optimal_end.date()} ({validation['optimal_period']['duration_days']} days)")

        # Test major planets that traditionally affect markets
        target_planets = ['Jupiter', 'Saturn', 'Mars', 'Venus', 'Mercury', 'Sun']

        # Run the backtest with real data
        results = await tester.backtest_patterns(optimal_start, optimal_end, target_planets)

        # Print comprehensive results
        print_real_oil_results(results, validation)

        # Save results with real data context
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"real_wti_lunar_backtest_{timestamp}.json"

        export_data = {
            'test_info': {
                'market': 'WTI_CRUDE_OIL',
                'data_type': 'real_prices',
                'start_date': results['test_period']['start'].isoformat(),
                'end_date': results['test_period']['end'].isoformat(),
                'total_events': results['total_events'],
                'patterns_discovered': results['discovered_patterns'],
                'data_validation': validation
            },
            'patterns': []
        }

        for pattern in results['patterns']:
            pattern_data = {
                'description': pattern.description,
                'aspect_type': pattern.aspect_type.value,
                'target_planet': pattern.target_planet,
                'consistency_rate': pattern.consistency_rate,
                'avg_magnitude': pattern.avg_magnitude,
                'avg_duration': pattern.avg_duration,
                'total_occurrences': pattern.total_occurrences,
                'last_occurrence': pattern.last_occurrence.isoformat(),
                'expected_value': pattern.consistency_rate * pattern.avg_magnitude
            }

            # Add sign information if available
            if hasattr(pattern, 'target_sign') and pattern.target_sign:
                pattern_data.update({
                    'target_sign': pattern.target_sign.sign_name,
                    'target_sign_element': pattern.target_sign.element,
                    'target_sign_quality': pattern.target_sign.quality,
                    'planetary_strength': getattr(pattern, 'pattern_strength', 'neutral')
                })

            export_data['patterns'].append(pattern_data)

        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"\\n💾 Real oil price results saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

        # Summary assessment
        if results['patterns']:
            total_expected_value = sum(p.consistency_rate * p.avg_magnitude for p in results['patterns'])
            print(f"\\n🎉 SUCCESS: Found {len(results['patterns'])} significant lunar patterns in real WTI oil data!")
            print(f"💰 Combined Expected Value: +{total_expected_value:.2f}% from all patterns")
            print("\\n🚀 These patterns could potentially be used for:")
            print("   - Oil futures trading signals")
            print("   - Portfolio hedging strategies")
            print("   - Market timing for oil-related investments")
        else:
            print(f"\\n🤔 No statistically significant patterns found in real oil data.")
            print("Consider:")
            print("   - Testing different time periods")
            print("   - Adjusting consistency thresholds")
            print("   - Testing other commodities (gold, natural gas)")

        return results

    except Exception as e:
        logger.error(f"Real oil backtest failed: {e}")
        print(f"\\n❌ Real oil backtest failed: {e}")
        return None
    finally:
        if tester.conn:
            tester.conn.close()

async def main():
    """Main execution function"""
    print("🚀 Starting Real WTI Oil Price Lunar Pattern Analysis")
    print("Using actual market data instead of synthetic data...")

    # Run comprehensive backtest (20 years of data)
    results = await run_real_oil_backtest('comprehensive')

    if results:
        print("\\n✅ Analysis complete! Check the saved JSON file for detailed results.")
    else:
        print("\\n❌ Analysis failed. Check logs for details.")

if __name__ == "__main__":
    # Run the real oil price lunar pattern backtest
    asyncio.run(main())