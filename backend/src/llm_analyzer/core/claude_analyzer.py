"""
Claude API integration for astrological trading analysis.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import anthropic

from ..models.trading_data import TradingOpportunity, LLMAnalysisRequest

logger = logging.getLogger(__name__)


class ClaudeAnalyzer:
    """Analyzes trading opportunities using Claude API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude client."""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or api_key parameter required")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info("✅ Claude API client initialized")

    def analyze_trading_patterns(
        self,
        prompt: str,
        model: str = "claude-3-sonnet-20240229",
        max_tokens: int = 4000,
        temperature: float = 0.1
    ) -> str:
        """Analyze trading patterns using Claude API."""

        try:
            logger.info("🤖 Querying Claude for astrological trading pattern analysis...")
            logger.info(f"📊 Prompt length: {len(prompt)} characters")

            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response = message.content[0].text if message.content else "No response from Claude"

            logger.info(f"✅ Received Claude analysis: {len(response)} characters")
            return response

        except Exception as e:
            logger.error(f"❌ Error querying Claude API: {e}")
            raise

    def analyze_comprehensive_oil_patterns(
        self,
        opportunities: List[TradingOpportunity],
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Perform comprehensive oil trading analysis with multiple focused queries."""

        if not focus_areas:
            focus_areas = ['comprehensive', 'lunar_phases', 'planetary_aspects']

        from ..prompts.oil_trading_prompts import OilTradingPrompts

        results = {}

        try:
            if 'comprehensive' in focus_areas:
                logger.info("🔍 Analyzing comprehensive oil trading patterns...")
                comprehensive_prompt = OilTradingPrompts.generate_comprehensive_oil_analysis_prompt(opportunities)
                results['comprehensive_analysis'] = self.analyze_trading_patterns(comprehensive_prompt)

            if 'lunar_phases' in focus_areas:
                logger.info("🌙 Analyzing lunar phase patterns...")
                lunar_prompt = OilTradingPrompts.generate_lunar_phase_analysis_prompt(opportunities)
                results['lunar_phase_analysis'] = self.analyze_trading_patterns(lunar_prompt)

            if 'planetary_aspects' in focus_areas:
                logger.info("⭐ Analyzing planetary aspect patterns...")
                aspects_prompt = OilTradingPrompts.generate_planetary_aspects_prompt(opportunities)
                results['planetary_aspects_analysis'] = self.analyze_trading_patterns(aspects_prompt)

            logger.info(f"✅ Completed {len(results)} focused analyses")
            return results

        except Exception as e:
            logger.error(f"❌ Error in comprehensive analysis: {e}")
            raise

    def store_analysis_results(
        self,
        analysis_results: Dict[str, str],
        output_file: str = None
    ) -> str:
        """Store analysis results to file."""

        if not output_file:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"/tmp/claude_oil_trading_analysis_{timestamp}.md"

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Claude AI Analysis: Astrological Patterns in Oil Futures Trading\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                for analysis_type, content in analysis_results.items():
                    f.write(f"## {analysis_type.replace('_', ' ').title()}\n\n")
                    f.write(content)
                    f.write("\n\n" + "="*80 + "\n\n")

            logger.info(f"✅ Analysis results saved to {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"❌ Error saving analysis results: {e}")
            raise

    def get_quick_insights(self, opportunities: List[TradingOpportunity]) -> str:
        """Get quick insights for immediate use."""

        # Create a condensed prompt for quick analysis
        quick_prompt = f"""
# Quick Oil Trading Astrological Insights

Analyze these {len(opportunities)} profitable oil futures trades and provide immediate actionable insights:

## Top 5 Trades by Astrological Score:
"""

        # Add top 5 trades
        top_trades = sorted(opportunities, key=lambda x: x.astrological_score, reverse=True)[:5]
        for i, trade in enumerate(top_trades, 1):
            quick_prompt += f"""
{i}. {trade.symbol} {trade.position_type.upper()} - {trade.profit_percent:.1f}% profit (Score: {trade.astrological_score}/100)
   Entry: {trade.entry_astro_description[:100]}...
"""

        quick_prompt += """

## Quick Questions:
1. What are the top 3 astrological indicators for profitable oil trades?
2. Which lunar phase is most favorable for oil trading?
3. What planetary aspects should oil traders watch for?
4. Give 3 specific trading rules based on this data.

Keep the response concise and actionable.
"""

        return self.analyze_trading_patterns(quick_prompt, max_tokens=2000)