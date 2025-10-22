"""
Main analyzer orchestrating data retrieval, prompt generation, and LLM analysis.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from .data_retriever import TradingDataRetriever
from .claude_analyzer import ClaudeAnalyzer
from .batch_processor import BatchAstroProcessor
from ..models.trading_data import TradingOpportunity

logger = logging.getLogger(__name__)


class OilTradingAstroAnalyzer:
    """Main analyzer for oil trading astrological patterns."""

    def __init__(self, db_config: Optional[Dict[str, str]] = None, claude_api_key: Optional[str] = None):
        """Initialize analyzer with data retriever and Claude client."""
        self.data_retriever = TradingDataRetriever(db_config)
        self.claude_analyzer = ClaudeAnalyzer(claude_api_key)
        self.batch_processor = BatchAstroProcessor()

    def run_comprehensive_analysis(
        self,
        analysis_types: Optional[List[str]] = None,
        output_dir: str = "/tmp",
        min_astro_score: float = None
    ) -> Dict[str, Any]:
        """Run complete astrological analysis of oil trading opportunities."""

        logger.info("🌟 Starting Comprehensive Oil Trading Astrological Analysis")

        # Retrieve trading data
        logger.info("📊 Retrieving trading opportunities from database...")
        opportunities = self.data_retriever.get_all_trading_opportunities()

        if not opportunities:
            logger.error("❌ No trading opportunities found with astrological data")
            return {'error': 'No trading opportunities found'}

        # Filter by astrological score if specified
        if min_astro_score:
            opportunities = [opp for opp in opportunities if opp.astrological_score >= min_astro_score]
            logger.info(f"🎯 Filtered to {len(opportunities)} opportunities with astrological score >= {min_astro_score}")

        # Get trading statistics
        stats = self.data_retriever.get_trading_statistics()
        logger.info(f"📈 Dataset: {stats['total_trades']} trades, avg profit: {stats['avg_profit']:.1f}%")

        # Perform Claude analysis
        logger.info("🤖 Performing Claude AI analysis...")
        analysis_results = self.claude_analyzer.analyze_comprehensive_oil_patterns(
            opportunities,
            analysis_types or ['comprehensive', 'lunar_phases', 'planetary_aspects']
        )

        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f"oil_trading_astro_analysis_{timestamp}.md")
        saved_file = self.claude_analyzer.store_analysis_results(analysis_results, output_file)

        # Create summary report
        summary = {
            'analysis_timestamp': datetime.now().isoformat(),
            'opportunities_analyzed': len(opportunities),
            'dataset_statistics': stats,
            'analysis_types_completed': list(analysis_results.keys()),
            'output_file': saved_file,
            'claude_analyses': analysis_results
        }

        logger.info("✅ Comprehensive analysis completed successfully")
        return summary

    def get_quick_trading_insights(self) -> str:
        """Get immediate actionable insights for oil trading."""

        logger.info("⚡ Generating quick trading insights...")

        # Get top-scoring opportunities
        opportunities = self.data_retriever.get_opportunities_by_criteria(
            min_astro_score=60.0,
            limit=10
        )

        if not opportunities:
            logger.warning("⚠️ No high-scoring opportunities found")
            return "No high-scoring astrological opportunities available for analysis."

        insights = self.claude_analyzer.get_quick_insights(opportunities)
        logger.info("✅ Quick insights generated")

        return insights

    def analyze_specific_patterns(
        self,
        pattern_type: str,
        criteria: Dict[str, Any] = None
    ) -> str:
        """Analyze specific astrological patterns."""

        logger.info(f"🔍 Analyzing {pattern_type} patterns...")

        # Get opportunities based on criteria
        opportunities = self.data_retriever.get_opportunities_by_criteria(**(criteria or {}))

        if not opportunities:
            return f"No trading opportunities found matching criteria for {pattern_type} analysis."

        from ..prompts.oil_trading_prompts import OilTradingPrompts

        if pattern_type == 'lunar_phases':
            prompt = OilTradingPrompts.generate_lunar_phase_analysis_prompt(opportunities)
        elif pattern_type == 'planetary_aspects':
            prompt = OilTradingPrompts.generate_planetary_aspects_prompt(opportunities)
        else:
            prompt = OilTradingPrompts.generate_comprehensive_oil_analysis_prompt(opportunities)

        analysis = self.claude_analyzer.analyze_trading_patterns(prompt)
        logger.info(f"✅ {pattern_type} analysis completed")

        return analysis

    def generate_trading_calendar(self) -> str:
        """Generate an astrological trading calendar for oil futures."""

        logger.info("📅 Generating astrological trading calendar...")

        opportunities = self.data_retriever.get_all_trading_opportunities()

        calendar_prompt = f"""
# Astrological Trading Calendar for Oil Futures

Based on {len(opportunities)} profitable oil trading opportunities, create a practical trading calendar.

## Data Summary:
"""

        # Add monthly breakdown
        monthly_data = {}
        for opp in opportunities:
            month = opp.entry_date.strftime('%B')
            if month not in monthly_data:
                monthly_data[month] = []
            monthly_data[month].append(opp)

        for month, trades in sorted(monthly_data.items()):
            avg_profit = sum(t.profit_percent for t in trades) / len(trades)
            calendar_prompt += f"- {month}: {len(trades)} trades, {avg_profit:.1f}% avg profit\n"

        calendar_prompt += """

## Calendar Request:
Create a month-by-month astrological trading calendar for oil futures with:

1. **Best months for oil trading** based on historical success
2. **Optimal lunar phases** for entering positions each month
3. **Planetary aspects to watch** throughout the year
4. **Seasonal patterns** in oil price movements
5. **Warning periods** to avoid trading

Format as a practical calendar that oil traders can reference daily.
"""

        calendar = self.claude_analyzer.analyze_trading_patterns(calendar_prompt)
        logger.info("✅ Trading calendar generated")

        return calendar

    def export_analysis_report(
        self,
        include_raw_data: bool = False,
        output_format: str = 'markdown'
    ) -> str:
        """Export comprehensive analysis report."""

        logger.info("📋 Generating comprehensive analysis report...")

        # Run all analyses
        summary = self.run_comprehensive_analysis()

        if 'error' in summary:
            return f"Error generating report: {summary['error']}"

        # Add trading calendar
        calendar = self.generate_trading_calendar()

        # Create comprehensive report
        report_content = f"""# Complete Oil Futures Astrological Trading Analysis

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Total Trades Analyzed:** {summary['opportunities_analyzed']}
- **Average Profit:** {summary['dataset_statistics']['avg_profit']:.1f}%
- **Average Astrological Score:** {summary['dataset_statistics']['avg_astrological_score']:.1f}/100
- **Date Range:** {summary['dataset_statistics']['earliest_trade']} to {summary['dataset_statistics']['latest_trade']}

## Astrological Trading Calendar

{calendar}

## Detailed Analysis

"""

        # Add all Claude analyses
        for analysis_type, content in summary['claude_analyses'].items():
            report_content += f"\n### {analysis_type.replace('_', ' ').title()}\n\n{content}\n\n"

        # Save comprehensive report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"/tmp/complete_oil_astro_trading_report_{timestamp}.md"

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)

            logger.info(f"✅ Comprehensive report saved to {report_file}")
            return report_file

        except Exception as e:
            logger.error(f"❌ Error saving report: {e}")
            raise

    def run_batch_analysis_all_opportunities(self, batch_size: int = 50) -> Dict[str, Any]:
        """Run batch analysis on ALL trading opportunities and store insights in database."""
        logger.info("🚀 Starting batch analysis of ALL trading opportunities")

        summary = self.batch_processor.process_all_opportunities()

        if 'error' in summary:
            logger.error(f"❌ Batch analysis failed: {summary['error']}")
            return summary

        logger.info(f"✅ Batch analysis completed: {summary['opportunities_analyzed']} opportunities processed")
        logger.info(f"💾 Extracted {summary['insights_extracted']} insights and stored in database")

        return summary

    def get_batch_processing_status(self) -> Dict[str, Any]:
        """Get current status of batch processing and insights storage."""
        return self.batch_processor.get_processing_status()