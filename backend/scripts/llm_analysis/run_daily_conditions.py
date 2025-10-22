#!/usr/bin/env python3
"""
Calculate and store daily astrological conditions for trading analysis.
Can be run for single days, date ranges, or as a daily job.
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

from llm_analyzer.core.daily_conditions import DailyAstrologyCalculator


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/daily_conditions.log') if os.path.exists('/tmp') else logging.NullHandler()
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
        description='Calculate and store daily astrological conditions for trading analysis'
    )

    parser.add_argument(
        '--date',
        type=parse_date,
        default=None,
        help='Specific date to calculate (YYYY-MM-DD). Default: today'
    )

    parser.add_argument(
        '--start-date',
        type=parse_date,
        default=None,
        help='Start date for range calculation (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end-date',
        type=parse_date,
        default=None,
        help='End date for range calculation (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--days-back',
        type=int,
        default=None,
        help='Calculate conditions for last N days from today'
    )

    parser.add_argument(
        '--days-forward',
        type=int,
        default=None,
        help='Calculate conditions for next N days from today'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--display-only',
        action='store_true',
        help='Display conditions without storing in database'
    )

    parser.add_argument(
        '--output-file',
        type=str,
        default=None,
        help='Save conditions to JSON file instead of database (for local testing)'
    )

    parser.add_argument(
        '--test-db',
        action='store_true',
        help='Test database connection only'
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Initialize calculator
        logger.info("🌟 Initializing Daily Astrology Calculator...")
        calculator = DailyAstrologyCalculator()

        # Test database connection if requested
        if args.test_db:
            logger.info("🔍 Testing database connection...")
            if calculator.test_database_connection():
                print("✅ Database connection successful!")
                return 0
            else:
                print("❌ Database connection failed!")
                return 1

        # Determine date range
        if args.start_date and args.end_date:
            start_date = args.start_date
            end_date = args.end_date
            mode = "range"
        elif args.days_back:
            end_date = date.today()
            start_date = end_date - timedelta(days=args.days_back - 1)
            mode = "range"
        elif args.days_forward:
            start_date = date.today()
            end_date = start_date + timedelta(days=args.days_forward - 1)
            mode = "range"
        else:
            target_date = args.date or date.today()
            mode = "single"

        if mode == "single":
            # Single date calculation
            logger.info(f"📅 Calculating conditions for {target_date}")

            conditions = calculator.calculate_daily_conditions(target_date)

            if 'error' in conditions:
                print(f"❌ Error: {conditions['error']}")
                return 1

            # Display results
            print("\n" + "="*80)
            print(f"🌟 ASTROLOGICAL CONDITIONS FOR {target_date}")
            print("="*80)
            print(f"📊 Daily Score: {conditions['daily_score']}/100")
            print(f"📈 Market Outlook: {conditions['market_outlook'].upper()}")
            print(f"🌙 Lunar Phase: {conditions['lunar_phase_name']} ({conditions['lunar_phase_angle']:.1f}°)")

            print(f"\n⭐ Major Aspects ({len(conditions['major_aspects'])}):")
            for aspect in conditions['major_aspects'][:10]:  # Show top 10
                exact = " (EXACT)" if aspect.get('exact') else f" ({aspect['orb']:.1f}° orb)"
                print(f"  - {aspect['planet1']} {aspect['aspect']} {aspect['planet2']}{exact}")

            print(f"\n🌍 Planetary Positions:")
            for planet, pos in conditions['planetary_positions'].items():
                if 'error' not in pos:
                    print(f"  - {planet}: {pos['formatted']}")

            if conditions['significant_events']:
                print(f"\n🎯 Significant Events:")
                for event in conditions['significant_events']:
                    print(f"  - {event}")

            if args.output_file:
                # Save to file
                success = calculator.save_conditions_to_file(conditions, args.output_file)
                if success:
                    print(f"\n💾 Conditions saved to file: {args.output_file}")
                else:
                    print(f"\n❌ Failed to save conditions to file")
                    return 1
            elif not args.display_only:
                # Store in database
                success = calculator.store_daily_conditions(conditions)
                if success:
                    print(f"\n💾 Conditions stored in database successfully")
                else:
                    print(f"\n❌ Failed to store conditions in database")
                    return 1

        else:
            # Date range calculation
            logger.info(f"📅 Calculating conditions from {start_date} to {end_date}")

            if args.display_only:
                print(f"\n🌟 DISPLAYING CONDITIONS (NOT STORING)")
                current = start_date
                while current <= end_date:
                    conditions = calculator.calculate_daily_conditions(current)
                    if 'error' not in conditions:
                        print(f"{current}: {conditions['daily_score']}/100 ({conditions['market_outlook']})")
                    else:
                        print(f"{current}: ERROR")
                    current += timedelta(days=1)
            else:
                summary = calculator.calculate_and_store_date_range(start_date, end_date)

                # Display results
                print("\n" + "="*80)
                print(f"🌟 DAILY CONDITIONS CALCULATION COMPLETED")
                print("="*80)
                print(f"📅 Date Range: {summary['start_date']} to {summary['end_date']}")
                print(f"📊 Total Days: {summary['total_days']}")
                print(f"✅ Successfully Processed: {summary['processed_successfully']}")
                print(f"❌ Errors: {summary['errors']}")
                print(f"📈 Success Rate: {summary['success_rate']:.1f}%")

                if summary['errors'] > 0:
                    print(f"\n⚠️ {summary['errors']} days had errors - check logs for details")

        print("\n📋 To view stored conditions:")
        print("SELECT trade_date, daily_score, market_outlook FROM daily_astrological_conditions ORDER BY trade_date DESC LIMIT 10;")
        print("="*80)

        logger.info("✅ Daily conditions calculation completed")
        return 0

    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())