#!/usr/bin/env python3
"""
Run batch analysis on ALL trading opportunities and store insights in database.
This script processes all trading opportunities in manageable batches.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add backend/src to path for imports
backend_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(backend_src))

from llm_analyzer.core.analyzer import OilTradingAstroAnalyzer


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/batch_analysis.log') if os.path.exists('/tmp') else logging.NullHandler()
        ]
    )


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Run batch analysis on ALL trading opportunities and store insights in database'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of opportunities to process per batch (default: 50)'
    )

    parser.add_argument(
        '--min-astro-score',
        type=float,
        default=None,
        help='Minimum astrological score to include (0-100)'
    )

    parser.add_argument(
        '--claude-api-key',
        type=str,
        default=None,
        help='Claude API key (or set ANTHROPIC_API_KEY env var)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--status-only',
        action='store_true',
        help='Only show current processing status, do not run analysis'
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Initialize analyzer
        logger.info("🌟 Initializing Oil Trading Astrological Batch Analyzer...")
        analyzer = OilTradingAstroAnalyzer(claude_api_key=args.claude_api_key)

        if args.status_only:
            # Show status only
            status = analyzer.get_batch_processing_status()

            print("\n" + "="*80)
            print("📊 CURRENT BATCH PROCESSING STATUS")
            print("="*80)

            if 'error' in status:
                print(f"❌ Error: {status['error']}")
                return 1

            print(f"📈 Total Opportunities: {status['total_opportunities']}")
            print(f"💡 Total Insights Stored: {status['total_insights']}")
            print(f"📊 Insights per Opportunity: {status['insights_per_opportunity']:.2f}")

            if status['latest_insight']:
                print(f"🕒 Latest Insight: {status['latest_insight']}")
            else:
                print("🕒 No insights stored yet")

            print("="*80)
            return 0

        # Run batch analysis
        logger.info(f"🚀 Starting batch analysis with batch size: {args.batch_size}")

        if args.min_astro_score:
            logger.info(f"🎯 Filtering to opportunities with astrological score >= {args.min_astro_score}")

        # Set batch size on processor
        analyzer.batch_processor.batch_size = args.batch_size

        summary = analyzer.run_batch_analysis_all_opportunities()

        if 'error' in summary:
            logger.error(f"❌ Batch analysis failed: {summary['error']}")
            return 1

        # Display results
        print("\n" + "="*100)
        print("🌟 BATCH ANALYSIS OF ALL TRADING OPPORTUNITIES COMPLETED")
        print("="*100)
        print(f"📊 Total Opportunities: {summary['total_opportunities']}")
        print(f"📦 Batches Processed: {summary['batches_processed']}")
        print(f"✅ Opportunities Analyzed: {summary['opportunities_analyzed']}")
        print(f"💡 Insights Extracted: {summary['insights_extracted']}")
        print(f"📋 Batch Size: {summary['batch_size']}")
        print(f"🕒 Processing Time: {summary['processing_time']}")

        # Get final status
        final_status = analyzer.get_batch_processing_status()
        print(f"\n📈 Final Database Status:")
        print(f"- Total Insights Stored: {final_status['total_insights']}")
        print(f"- Insights per Opportunity: {final_status['insights_per_opportunity']:.2f}")

        print("\n🎯 Next Steps:")
        print("1. Run daily conditions calculator to populate daily_astrological_conditions table")
        print("2. Implement daily recommendations engine")
        print("3. Create API endpoints for accessing insights and recommendations")

        print("\n📋 To view stored insights:")
        print("SELECT category, COUNT(*) FROM astrological_insights GROUP BY category;")
        print("SELECT pattern_name, confidence_score FROM astrological_insights ORDER BY confidence_score DESC LIMIT 10;")
        print("="*100)

        logger.info("✅ Batch analysis completed successfully")
        return 0

    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())