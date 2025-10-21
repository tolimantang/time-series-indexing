#!/usr/bin/env python3
"""
Run comprehensive astrological analysis of oil futures trading opportunities using Claude AI.
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
            logging.FileHandler('/tmp/oil_astro_analysis.log') if os.path.exists('/tmp') else logging.NullHandler()
        ]
    )


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Analyze oil futures trading opportunities with astrological data using Claude AI'
    )

    parser.add_argument(
        '--analysis-type',
        choices=['comprehensive', 'quick', 'lunar', 'aspects', 'calendar', 'full-report'],
        default='comprehensive',
        help='Type of analysis to perform'
    )

    parser.add_argument(
        '--min-astro-score',
        type=float,
        default=None,
        help='Minimum astrological score to include (0-100)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='/tmp',
        help='Output directory for analysis results'
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

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Initialize analyzer
        logger.info("🌟 Initializing Oil Trading Astrological Analyzer...")
        analyzer = OilTradingAstroAnalyzer(claude_api_key=args.claude_api_key)

        # Run analysis based on type
        if args.analysis_type == 'quick':
            logger.info("⚡ Running quick insights analysis...")
            insights = analyzer.get_quick_trading_insights()

            print("\n" + "="*80)
            print("⚡ QUICK OIL TRADING INSIGHTS")
            print("="*80)
            print(insights)
            print("\n" + "="*80)

        elif args.analysis_type == 'lunar':
            logger.info("🌙 Running lunar phase analysis...")
            analysis = analyzer.analyze_specific_patterns('lunar_phases')

            print("\n" + "="*80)
            print("🌙 LUNAR PHASE ANALYSIS")
            print("="*80)
            print(analysis)
            print("\n" + "="*80)

        elif args.analysis_type == 'aspects':
            logger.info("⭐ Running planetary aspects analysis...")
            analysis = analyzer.analyze_specific_patterns('planetary_aspects')

            print("\n" + "="*80)
            print("⭐ PLANETARY ASPECTS ANALYSIS")
            print("="*80)
            print(analysis)
            print("\n" + "="*80)

        elif args.analysis_type == 'calendar':
            logger.info("📅 Generating trading calendar...")
            calendar = analyzer.generate_trading_calendar()

            print("\n" + "="*80)
            print("📅 ASTROLOGICAL TRADING CALENDAR")
            print("="*80)
            print(calendar)
            print("\n" + "="*80)

        elif args.analysis_type == 'full-report':
            logger.info("📋 Generating full comprehensive report...")
            report_file = analyzer.export_analysis_report()

            print("\n" + "="*80)
            print("📋 FULL COMPREHENSIVE REPORT GENERATED")
            print("="*80)
            print(f"Report saved to: {report_file}")
            print("\nThis includes:")
            print("- Executive summary")
            print("- Comprehensive astrological analysis")
            print("- Lunar phase patterns")
            print("- Planetary aspect analysis")
            print("- Trading calendar")
            print("- Actionable trading rules")
            print("="*80)

        else:  # comprehensive
            logger.info("🔍 Running comprehensive analysis...")
            summary = analyzer.run_comprehensive_analysis(
                min_astro_score=args.min_astro_score,
                output_dir=args.output_dir
            )

            if 'error' in summary:
                logger.error(f"❌ Analysis failed: {summary['error']}")
                return 1

            print("\n" + "="*100)
            print("🌟 COMPREHENSIVE OIL TRADING ASTROLOGICAL ANALYSIS COMPLETED")
            print("="*100)
            print(f"📊 Analyzed {summary['opportunities_analyzed']} trading opportunities")
            print(f"📈 Average Profit: {summary['dataset_statistics']['avg_profit']:.1f}%")
            print(f"⭐ Average Astrological Score: {summary['dataset_statistics']['avg_astrological_score']:.1f}/100")
            print(f"📅 Date Range: {summary['dataset_statistics']['earliest_trade']} to {summary['dataset_statistics']['latest_trade']}")
            print(f"💾 Results saved to: {summary['output_file']}")

            print(f"\n🎯 Analysis Types Completed:")
            for analysis_type in summary['analysis_types_completed']:
                print(f"  ✅ {analysis_type.replace('_', ' ').title()}")

            print(f"\n📋 View detailed analysis in: {summary['output_file']}")
            print("="*100)

        logger.info("✅ Analysis completed successfully")
        return 0

    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())