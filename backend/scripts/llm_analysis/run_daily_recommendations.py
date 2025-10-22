#!/usr/bin/env python3
"""
Generate and store daily trading recommendations based on astrological conditions and insights.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, date, timedelta

# Add backend/src to path for imports
backend_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(backend_src))

from llm_analyzer.core.daily_recommendations import DailyTradingEngine


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/daily_recommendations.log') if os.path.exists('/tmp') else logging.NullHandler()
        ]
    )


def parse_date(date_string: str) -> date:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_string}. Use YYYY-MM-DD")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Generate daily trading recommendations based on astrological conditions'
    )

    parser.add_argument(
        '--date',
        type=parse_date,
        default=None,
        help='Specific date to generate recommendations (YYYY-MM-DD). Default: today'
    )

    parser.add_argument(
        '--latest',
        action='store_true',
        help='Show latest recommendations without generating new ones'
    )

    parser.add_argument(
        '--days-back',
        type=int,
        default=7,
        help='Number of days to look back for latest recommendations (default: 7)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Initialize trading engine
        logger.info("🌟 Initializing Daily Trading Engine...")
        engine = DailyTradingEngine()

        if args.latest:
            # Show latest recommendations
            recommendations = engine.get_latest_recommendations(args.days_back)

            print("\n" + "="*100)
            print(f"📈 LATEST TRADING RECOMMENDATIONS (Last {args.days_back} days)")
            print("="*100)

            if not recommendations:
                print("No recommendations found")
                return 0

            current_date = None
            for rec in recommendations:
                if rec['recommendation_date'] != current_date:
                    current_date = rec['recommendation_date']
                    print(f"\n📅 {current_date}")
                    print("-" * 60)

                confidence_icon = "🟢" if rec['confidence'] >= 70 else "🟡" if rec['confidence'] >= 50 else "🔴"
                action_icon = {
                    'enter_long': '📈',
                    'enter_short': '📉',
                    'hold': '⏸️',
                    'avoid': '⚠️'
                }.get(rec['recommendation_type'], '❓')

                print(f"{action_icon} {rec['symbol']}: {rec['recommendation_type'].upper()} "
                      f"{confidence_icon} {rec['confidence']:.0f}% confidence")
                print(f"   Reasoning: {rec['astrological_reasoning'][:80]}...")
                print(f"   Hold for: {rec['holding_period_days']} days")

            print("="*100)
            return 0

        # Generate recommendations for target date
        target_date = args.date or date.today()
        logger.info(f"🎯 Generating recommendations for {target_date}")

        summary = engine.generate_daily_recommendations(target_date)

        if 'error' in summary:
            print(f"❌ Error: {summary['error']}")
            return 1

        # Display results
        print("\n" + "="*100)
        print(f"🎯 DAILY TRADING RECOMMENDATIONS FOR {target_date}")
        print("="*100)

        conditions = summary['daily_conditions']
        print(f"🌟 Astrological Score: {conditions['score']}/100")
        print(f"📊 Market Outlook: {conditions['outlook'].upper()}")
        print(f"🌙 Lunar Phase: {conditions['lunar_phase']}")
        print(f"💡 Insights Used: {summary['insights_used']}")

        print(f"\n📈 Oil Futures Recommendations:")
        print("-" * 70)

        for rec in summary['recommendations']:
            confidence_icon = "🟢" if rec['confidence'] >= 70 else "🟡" if rec['confidence'] >= 50 else "🔴"
            action_icon = {
                'enter_long': '📈',
                'enter_short': '📉',
                'hold': '⏸️',
                'avoid': '⚠️'
            }.get(rec['recommendation_type'], '❓')

            print(f"{action_icon} {rec['symbol']}: {rec['recommendation_type'].upper()} "
                  f"{confidence_icon} {rec['confidence']:.0f}% confidence")
            print(f"   Reasoning: {rec['astrological_reasoning']}")
            print(f"   Suggested holding period: {rec['holding_period_days']} days")
            print()

        print(f"💾 Storage: {summary['recommendations_stored']}/{summary['recommendations_generated']} recommendations stored")

        print(f"\n🎯 Trading Summary:")
        long_recs = [r for r in summary['recommendations'] if r['recommendation_type'] == 'enter_long']
        short_recs = [r for r in summary['recommendations'] if r['recommendation_type'] == 'enter_short']
        avoid_recs = [r for r in summary['recommendations'] if r['recommendation_type'] == 'avoid']

        if long_recs:
            avg_confidence = sum(r['confidence'] for r in long_recs) / len(long_recs)
            print(f"📈 Long opportunities: {len(long_recs)} symbols (avg confidence: {avg_confidence:.0f}%)")

        if short_recs:
            avg_confidence = sum(r['confidence'] for r in short_recs) / len(short_recs)
            print(f"📉 Short opportunities: {len(short_recs)} symbols (avg confidence: {avg_confidence:.0f}%)")

        if avoid_recs:
            print(f"⚠️ Avoid trading: {len(avoid_recs)} symbols")

        print(f"\n📋 To view stored recommendations:")
        print("SELECT * FROM daily_trading_recommendations WHERE recommendation_date = CURRENT_DATE ORDER BY confidence DESC;")
        print("="*100)

        logger.info("✅ Daily recommendations generation completed")
        return 0

    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())