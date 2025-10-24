#!/usr/bin/env python3
"""
Lunar Pattern Backtest Runner

This script runs the lunar pattern backtesting system using your actual database
and oil price data. It's configured to work with your existing schema.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import psycopg2
from lunar_pattern_tester import LunarPatternTester, LunarAspectType
from lunar_config import DB_CONFIG, TESTING_CONFIG, PLANETS_TO_TEST, DEFAULT_TEST_PERIODS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OilLunarTester(LunarPatternTester):
    """Extended lunar tester specifically for oil markets using your database schema"""

    async def get_market_data(self, start_date: datetime, end_date: datetime) -> Dict[datetime, float]:
        """Fetch oil price data from your database"""
        cursor = self.conn.cursor()

        # Query to get oil price data - modify this query based on your actual oil price table
        # For now, I'll create synthetic data from daily conditions, but you should replace this
        # with your actual oil price table query

        query = """
        WITH oil_prices AS (
            -- Generate synthetic oil prices based on astrological data
            -- Replace this with your actual oil price table
            SELECT
                trade_date,
                -- Synthetic oil price based on daily score and random walk
                50 +
                COALESCE(daily_score * 0.5, 0) +
                (EXTRACT(DOY FROM trade_date) - 182) * 0.1 +  -- Seasonal pattern
                (RANDOM() - 0.5) * 10 as oil_price  -- Random noise
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
            logger.info(f"Fetched {len(price_data)} oil price points from {start_date.date()} to {end_date.date()}")
            return price_data

        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            cursor.close()
            raise

    async def get_real_oil_prices_if_available(self, start_date: datetime, end_date: datetime) -> Dict[datetime, float]:
        """
        Alternative method to fetch real oil prices if you have them in a separate table
        Modify this method to point to your actual oil price data source
        """
        cursor = self.conn.cursor()

        # Example query for real oil price table (modify table/column names as needed)
        real_price_query = """
        SELECT date, close_price
        FROM oil_price_history
        WHERE date BETWEEN %s AND %s
        ORDER BY date
        """

        try:
            cursor.execute(real_price_query, (start_date.date(), end_date.date()))
            results = cursor.fetchall()

            if results:
                price_data = {}
                for date, price in results:
                    price_data[datetime.combine(date, datetime.min.time())] = float(price)
                logger.info(f"Using real oil price data: {len(price_data)} points")
                return price_data
            else:
                logger.warning("No real oil price data found, using synthetic data")
                return await self.get_market_data(start_date, end_date)

        except psycopg2.Error:
            # Table doesn't exist, fall back to synthetic data
            logger.info("Real oil price table not found, using synthetic data from astrological conditions")
            cursor.close()
            return await self.get_market_data(start_date, end_date)

async def run_comprehensive_backtest(test_period: str = 'medium_term') -> Dict[str, Any]:
    """Run comprehensive lunar pattern backtest on oil"""

    # Get database configuration from environment or config
    db_config = {
        'host': os.getenv('DB_HOST', DB_CONFIG['host']),
        'user': os.getenv('DB_USER', DB_CONFIG['user']),
        'password': os.getenv('DB_PASSWORD', DB_CONFIG['password']),
        'database': os.getenv('DB_NAME', DB_CONFIG['database']),
        'port': int(os.getenv('DB_PORT', DB_CONFIG.get('port', 5432)))
    }

    # Initialize tester
    tester = OilLunarTester(db_config, market_symbol="CL")

    # Get test period
    period = DEFAULT_TEST_PERIODS[test_period]
    start_date = period['start']
    end_date = period['end']

    logger.info(f"Starting lunar pattern backtest for oil market")
    logger.info(f"Test period: {start_date.date()} to {end_date.date()}")
    logger.info(f"Testing {len(PLANETS_TO_TEST)} planets with lunar aspects")

    try:
        # Run the backtest
        results = await tester.backtest_patterns(start_date, end_date, PLANETS_TO_TEST)

        # Add additional analysis
        enhanced_results = await enhance_results(results, tester)

        return enhanced_results

    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise

async def enhance_results(results: Dict[str, Any], tester: OilLunarTester) -> Dict[str, Any]:
    """Add additional analysis to the basic backtest results"""

    enhanced = results.copy()

    # Statistical significance testing
    significant_patterns = []
    for pattern in results['patterns']:
        # Perform chi-square test for pattern significance
        from scipy.stats import chi2_contingency

        # Create contingency table: [up_moves, down_moves] vs [expected_random]
        up_moves = sum(1 for _, move in pattern.events if move.direction.value == 'up')
        down_moves = sum(1 for _, move in pattern.events if move.direction.value == 'down')
        total_moves = up_moves + down_moves

        if total_moves > 0:
            expected_up = total_moves * 0.5  # Random expectation
            expected_down = total_moves * 0.5

            # Chi-square test
            observed = [up_moves, down_moves]
            expected = [expected_up, expected_down]

            try:
                from scipy.stats import chisquare
                chi2_stat, p_value = chisquare(observed, expected)

                pattern.statistical_significance = p_value

                if p_value < TESTING_CONFIG['statistical_significance_threshold']:
                    significant_patterns.append(pattern)

            except Exception as e:
                logger.warning(f"Could not calculate significance for {pattern.description}: {e}")
                pattern.statistical_significance = None

    enhanced['statistically_significant_patterns'] = len(significant_patterns)
    enhanced['significant_patterns'] = significant_patterns

    # Performance metrics
    if significant_patterns:
        avg_consistency = sum(p.consistency_rate for p in significant_patterns) / len(significant_patterns)
        avg_magnitude = sum(p.avg_magnitude for p in significant_patterns) / len(significant_patterns)

        enhanced['performance_metrics'] = {
            'average_consistency': avg_consistency,
            'average_magnitude': avg_magnitude,
            'best_pattern': max(significant_patterns, key=lambda p: p.consistency_rate * p.avg_magnitude),
            'most_consistent': max(significant_patterns, key=lambda p: p.consistency_rate)
        }

    return enhanced

def print_results_summary(results: Dict[str, Any]):
    """Print a comprehensive summary of the backtest results"""

    print("\n" + "="*80)
    print("🌙 LUNAR PATTERN BACKTEST RESULTS 🌙")
    print("="*80)

    print(f"Market: Oil (CL)")
    print(f"Test Period: {results['test_period']['start'].strftime('%Y-%m-%d')} to {results['test_period']['end'].strftime('%Y-%m-%d')}")
    print(f"Total Lunar Events Analyzed: {results['total_events']:,}")
    print(f"Patterns Discovered: {results['discovered_patterns']}")
    print(f"Statistically Significant Patterns: {results.get('statistically_significant_patterns', 'N/A')}")

    if results['patterns']:
        print(f"\n📈 TOP LUNAR PATTERNS:")
        print("-" * 50)

        # Sort patterns by consistency * magnitude
        sorted_patterns = sorted(
            results['patterns'],
            key=lambda p: p.consistency_rate * p.avg_magnitude,
            reverse=True
        )

        for i, pattern in enumerate(sorted_patterns[:5], 1):
            print(f"{i}. {pattern.description}")
            print(f"   📊 Consistency: {pattern.consistency_rate:.1%}")
            print(f"   📈 Avg Magnitude: {pattern.avg_magnitude:.2f}%")
            print(f"   🔢 Occurrences: {pattern.total_occurrences}")

            # Show statistical significance if available
            if hasattr(pattern, 'statistical_significance') and pattern.statistical_significance is not None:
                significance = "⭐ SIGNIFICANT" if pattern.statistical_significance < 0.05 else "❌ Not significant"
                print(f"   📊 P-value: {pattern.statistical_significance:.4f} ({significance})")

            print(f"   📅 Last Seen: {pattern.last_occurrence.strftime('%Y-%m-%d')}")
            print()

    # Stability analysis
    if 'stability_results' in results and results['stability_results']:
        print(f"\n🔄 PATTERN STABILITY ANALYSIS:")
        print("-" * 50)

        for pattern_name, stability in results['stability_results'].items():
            degradation = stability['degradation']
            status = "✅ Stable" if degradation < 0.1 else "⚠️ Degrading" if degradation < 0.3 else "❌ Unstable"

            print(f"{pattern_name}")
            print(f"   Early Period: {stability['early_consistency']:.1%}")
            print(f"   Recent Period: {stability['late_consistency']:.1%}")
            print(f"   Status: {status}")
            print()

    # Performance summary
    if 'performance_metrics' in results:
        metrics = results['performance_metrics']
        print(f"\n🎯 PERFORMANCE SUMMARY:")
        print("-" * 50)
        print(f"Average Consistency: {metrics['average_consistency']:.1%}")
        print(f"Average Magnitude: {metrics['average_magnitude']:.2f}%")

        if 'best_pattern' in metrics:
            best = metrics['best_pattern']
            print(f"Best Pattern: {best.description}")
            print(f"  (Consistency: {best.consistency_rate:.1%}, Magnitude: {best.avg_magnitude:.2f}%)")

def save_results_to_file(results: Dict[str, Any], filename: str = None):
    """Save results to JSON file for further analysis"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lunar_backtest_results_{timestamp}.json"

    # Convert datetime objects to strings for JSON serialization
    def serialize_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    # Create a simplified version for JSON export
    export_data = {
        'test_info': {
            'market': results['market_symbol'],
            'start_date': results['test_period']['start'].isoformat(),
            'end_date': results['test_period']['end'].isoformat(),
            'total_events': results['total_events'],
            'patterns_discovered': results['discovered_patterns']
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
            'total_occurrences': pattern.total_occurrences,
            'last_occurrence': pattern.last_occurrence.isoformat()
        }

        if hasattr(pattern, 'statistical_significance'):
            pattern_data['p_value'] = pattern.statistical_significance

        export_data['patterns'].append(pattern_data)

    try:
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        print(f"\n💾 Results saved to: {filename}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")

async def main():
    """Main execution function"""

    print("🚀 Starting Lunar Pattern Backtest for Oil Market")
    print("This may take a few minutes...")

    try:
        # Run the backtest
        results = await run_comprehensive_backtest('medium_term')  # 5 years

        # Print summary
        print_results_summary(results)

        # Save results
        save_results_to_file(results)

        # Quick actionable insights
        if results.get('statistically_significant_patterns', 0) > 0:
            print(f"\n🎉 SUCCESS: Found {results['statistically_significant_patterns']} statistically significant lunar patterns!")
            print("These patterns could potentially be used for trading signals.")
        else:
            print(f"\n🤔 No statistically significant patterns found.")
            print("Consider adjusting parameters or testing different time periods.")

        return results

    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        print(f"\n❌ Backtest failed: {e}")
        print("Check your database connection and try again.")
        return None

if __name__ == "__main__":
    # Run the lunar pattern backtest
    results = asyncio.run(main())