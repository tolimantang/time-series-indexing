#!/usr/bin/env python3
"""
Trading Opportunity Astrological Correlation Analysis
Analyzes astrological patterns associated with profitable trading opportunities.

This script:
1. Retrieves trading opportunities from the database
2. Gets astrological data for the corresponding trading periods
3. Uses LLM analysis to identify astrological patterns
4. Generates insights about astro-trading correlations
"""

import os
import sys
import argparse
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any
import json

# Add backend/src to path for imports
backend_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(backend_src))

from astro_encoder.core.encoder import AstroEncoder
from astro_encoder.core.data_access import AstroDataAccess
from astro_encoder.core.verbalizer import AstroVerbalizer


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/astro_trading_analysis.log') if os.path.exists('/tmp') else logging.NullHandler()
        ]
    )


class TradingAstroAnalyzer:
    """Analyzes astrological correlations with trading opportunities."""

    def __init__(self):
        """Initialize the analyzer."""
        self.astro_encoder = AstroEncoder()
        self.astro_data_access = AstroDataAccess()
        self.verbalizer = AstroVerbalizer()

        # Create tables if needed
        try:
            self.astro_data_access.create_astro_tables()
        except Exception as e:
            logging.warning(f"Could not create astro tables: {e}")

    def get_trading_opportunities(self, symbol: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve trading opportunities from database."""
        try:
            import psycopg2

            db_config = {
                'host': os.getenv('DB_HOST'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME'),
                'user': os.getenv('DB_USER'),
                'password': os.getenv('DB_PASSWORD'),
            }

            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()

            # Query trading opportunities
            query = """
                SELECT symbol, position_type, entry_date, exit_date,
                       entry_price, exit_price, holding_days, profit_percent, trade_score
                FROM trading_opportunities
            """
            params = []

            if symbol:
                query += " WHERE symbol = %s"
                params.append(symbol)

            query += " ORDER BY trade_score DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            results = []

            for row in cursor.fetchall():
                results.append({
                    'symbol': row[0],
                    'position_type': row[1],
                    'entry_date': row[2],
                    'exit_date': row[3],
                    'entry_price': float(row[4]),
                    'exit_price': float(row[5]),
                    'holding_days': row[6],
                    'profit_percent': float(row[7]),
                    'trade_score': float(row[8])
                })

            cursor.close()
            conn.close()

            logging.info(f"Retrieved {len(results)} trading opportunities")
            return results

        except Exception as e:
            logging.error(f"Error retrieving trading opportunities: {e}")
            return []

    def ensure_astrological_data(self, start_date: date, end_date: date) -> None:
        """Ensure astrological data exists for the date range."""
        logging.info(f"Ensuring astrological data for {start_date} to {end_date}")

        try:
            # Get missing dates
            missing_dates = self.astro_data_access.get_missing_dates(start_date, end_date)

            if missing_dates:
                logging.info(f"Calculating astrological data for {len(missing_dates)} missing dates")

                for missing_date in missing_dates:
                    try:
                        # Calculate astrological data
                        dt = datetime.combine(missing_date, datetime.min.time())
                        astro_data = self.astro_encoder.encode_date(dt, location='universal')

                        # Generate descriptions
                        daily_description = self.verbalizer.verbalize_daily_data(astro_data)
                        market_interpretation = self._generate_market_interpretation(astro_data)

                        # Store in database
                        self.astro_data_access.store_astrological_data(
                            astro_data,
                            daily_description,
                            market_interpretation
                        )

                        logging.info(f"✅ Processed astrological data for {missing_date}")

                    except Exception as e:
                        logging.error(f"❌ Error processing {missing_date}: {e}")
                        continue
            else:
                logging.info("All astrological data already exists")

        except Exception as e:
            logging.error(f"Error ensuring astrological data: {e}")

    def _generate_market_interpretation(self, astro_data) -> str:
        """Generate basic market interpretation."""
        # This is a simplified interpretation - could be enhanced with more sophisticated analysis
        interpretations = []

        # Check lunar phase for volatility
        if astro_data.lunar_phase:
            phase = astro_data.lunar_phase % 360
            if 135 <= phase < 225:  # Full moon
                interpretations.append("high volatility period")
            elif 0 <= phase < 45 or 315 <= phase < 360:  # New moon
                interpretations.append("new trend initiation period")

        # Check for major aspects
        major_aspects = [a for a in astro_data.aspects if a.aspect_type in ['conjunction', 'opposition', 'square'] and a.exactness > 0.8]
        if major_aspects:
            interpretations.append("significant astrological pressure")

        return "; ".join(interpretations) if interpretations else "neutral astrological conditions"

    def analyze_trading_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze astrological patterns for a single trading opportunity."""
        entry_date = opportunity['entry_date']
        exit_date = opportunity['exit_date']

        # Get astrological data for the trading period
        astro_data_list = self.astro_data_access.get_astrological_data_for_trading_period(
            entry_date, exit_date
        )

        if not astro_data_list:
            return {
                'opportunity': opportunity,
                'astrological_summary': 'No astrological data available',
                'entry_conditions': 'Unknown',
                'exit_conditions': 'Unknown',
                'period_highlights': 'Unknown'
            }

        # Generate comprehensive astrological analysis
        entry_conditions = astro_data_list[0]['daily_description'] if astro_data_list else 'Unknown'
        exit_conditions = astro_data_list[-1]['daily_description'] if len(astro_data_list) > 1 else 'Same as entry'

        # Collect significant events during the period
        all_events = []
        for data in astro_data_list:
            if data['significant_events']:
                all_events.extend(data['significant_events'])

        period_highlights = '; '.join(list(set(all_events))[:5]) if all_events else 'No significant events'

        # Create summary for LLM analysis
        summary_parts = [
            f"Trading: {opportunity['position_type'].upper()} {opportunity['symbol']} "
            f"from {entry_date} to {exit_date} ({opportunity['holding_days']} days)",
            f"Profit: {opportunity['profit_percent']:.2f}% (Score: {opportunity['trade_score']:.1f})",
            f"Entry conditions: {entry_conditions}",
            f"Exit conditions: {exit_conditions}",
            f"Period events: {period_highlights}"
        ]

        return {
            'opportunity': opportunity,
            'astrological_summary': ' | '.join(summary_parts),
            'entry_conditions': entry_conditions,
            'exit_conditions': exit_conditions,
            'period_highlights': period_highlights
        }

    def generate_llm_analysis_prompt(self, analyzed_opportunities: List[Dict[str, Any]]) -> str:
        """Generate prompt for LLM analysis of astrological patterns."""

        # Group by position type
        long_trades = [a for a in analyzed_opportunities if a['opportunity']['position_type'] == 'long']
        short_trades = [a for a in analyzed_opportunities if a['opportunity']['position_type'] == 'short']

        prompt_parts = [
            "# Astrological Analysis of Profitable Trading Opportunities",
            "",
            "Please analyze the following trading opportunities and their associated astrological conditions to identify patterns.",
            "",
            "## Task:",
            "1. Identify common astrological themes in successful LONG positions",
            "2. Identify common astrological themes in successful SHORT positions",
            "3. Look for patterns in entry timing, exit timing, and holding periods",
            "4. Suggest astrological indicators that might signal good entry/exit points",
            "5. Note any lunar phase correlations with profitability",
            "",
            "## Long Position Opportunities:",
            ""
        ]

        # Add long trades
        for i, analysis in enumerate(long_trades[:10], 1):
            prompt_parts.append(f"{i}. {analysis['astrological_summary']}")

        prompt_parts.extend([
            "",
            "## Short Position Opportunities:",
            ""
        ])

        # Add short trades
        for i, analysis in enumerate(short_trades[:10], 1):
            prompt_parts.append(f"{i}. {analysis['astrological_summary']}")

        prompt_parts.extend([
            "",
            "## Analysis Request:",
            "Based on these successful trades, what astrological patterns do you observe?",
            "What planetary positions, aspects, or lunar phases appear most frequently",
            "in profitable trades? Are there differences between long and short position timing?",
            "Please provide specific, actionable insights for future trading decisions."
        ])

        return "\n".join(prompt_parts)

    def run_analysis(
        self,
        symbol: str = None,
        limit: int = 50,
        ensure_astro_data: bool = True
    ) -> Dict[str, Any]:
        """Run complete astrological correlation analysis."""

        logging.info("🌟 Starting Trading-Astrological Correlation Analysis")

        # Get trading opportunities
        opportunities = self.get_trading_opportunities(symbol, limit)
        if not opportunities:
            logging.error("No trading opportunities found")
            return {'error': 'No trading opportunities found'}

        # Determine date range needed
        all_dates = []
        for opp in opportunities:
            all_dates.extend([opp['entry_date'], opp['exit_date']])

        start_date = min(all_dates)
        end_date = max(all_dates)

        logging.info(f"Date range: {start_date} to {end_date}")

        # Ensure astrological data exists
        if ensure_astro_data:
            self.ensure_astrological_data(start_date, end_date)

        # Analyze each opportunity
        analyzed_opportunities = []
        for i, opportunity in enumerate(opportunities, 1):
            logging.info(f"Analyzing opportunity {i}/{len(opportunities)}: "
                        f"{opportunity['symbol']} {opportunity['position_type']}")

            analysis = self.analyze_trading_opportunity(opportunity)
            analyzed_opportunities.append(analysis)

        # Generate LLM analysis prompt
        llm_prompt = self.generate_llm_analysis_prompt(analyzed_opportunities)

        # Save results
        results = {
            'analysis_date': datetime.now().isoformat(),
            'symbol_filter': symbol,
            'opportunities_analyzed': len(analyzed_opportunities),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'analyzed_opportunities': analyzed_opportunities,
            'llm_analysis_prompt': llm_prompt
        }

        # Save to file
        output_file = f"/tmp/astro_trading_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logging.info(f"✅ Results saved to {output_file}")
        except Exception as e:
            logging.error(f"Error saving results: {e}")

        return results


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Analyze Astrological Correlations with Trading Opportunities')
    parser.add_argument('--symbol', type=str, help='Filter by symbol (e.g., CRUDE_OIL_WTI)')
    parser.add_argument('--limit', type=int, default=50, help='Number of top opportunities to analyze')
    parser.add_argument('--skip-astro-calculation', action='store_true',
                       help='Skip astrological data calculation (use existing data only)')

    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        analyzer = TradingAstroAnalyzer()
        results = analyzer.run_analysis(
            symbol=args.symbol,
            limit=args.limit,
            ensure_astro_data=not args.skip_astro_calculation
        )

        if 'error' not in results:
            print("\n" + "="*80)
            print("🌟 ASTROLOGICAL TRADING CORRELATION ANALYSIS COMPLETED")
            print("="*80)
            print(f"Analyzed {results['opportunities_analyzed']} trading opportunities")
            print(f"Date range: {results['date_range']['start']} to {results['date_range']['end']}")

            print("\n📋 LLM ANALYSIS PROMPT:")
            print("-"*80)
            print(results['llm_analysis_prompt'])
            print("-"*80)

            print("\n💡 Next Steps:")
            print("1. Copy the LLM analysis prompt above")
            print("2. Submit it to Claude Sonnet or another LLM")
            print("3. Review the astrological patterns identified")
            print("4. Use insights for future trading decisions")

        return 0

    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())