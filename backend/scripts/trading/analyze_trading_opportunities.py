#!/usr/bin/env python3
"""
Trading Opportunity Analysis Script
Analyzes historical market data to identify profitable trading opportunities.

Usage:
    python scripts/trading/analyze_trading_opportunities.py --config config/trading_config.yaml
    python scripts/trading/analyze_trading_opportunities.py --symbols CRUDE_OIL_WTI --top-trades 20
    python scripts/trading/analyze_trading_opportunities.py --symbols CRUDE_OIL_WTI CRUDE_OIL_BRENT --output json
"""

import os
import sys
import argparse
import yaml
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add backend/src to path for imports
backend_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(backend_src))

from trading_analyzer.core.opportunity_detector import TradingOpportunityDetector, TradeOpportunity
from trading_analyzer.core.data_access import MarketDataAccess


def setup_logging(config: Dict[str, Any]) -> None:
    """Setup logging configuration."""
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO').upper())
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/trading_analysis.log') if os.path.exists('/tmp') else logging.NullHandler()
        ]
    )


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logging.info(f"Loaded configuration from {config_path}")
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML configuration: {e}")
        raise


def opportunity_to_dict(opportunity: TradeOpportunity) -> Dict[str, Any]:
    """Convert TradeOpportunity object to dictionary for serialization."""
    return {
        'symbol': opportunity.symbol,
        'position_type': opportunity.position_type,
        'entry_date': opportunity.entry_date.isoformat() if opportunity.entry_date else None,
        'exit_date': opportunity.exit_date.isoformat() if opportunity.exit_date else None,
        'entry_price': opportunity.entry_price,
        'exit_price': opportunity.exit_price,
        'holding_days': opportunity.holding_days,
        'profit_percent': round(opportunity.profit_percent, 4),
        'max_unrealized_gain_percent': round(opportunity.max_unrealized_gain_percent, 4),
        'max_unrealized_loss_percent': round(opportunity.max_unrealized_loss_percent, 4),
        'max_drawdown_from_peak': round(opportunity.max_drawdown_from_peak, 4),
        'peak_profit_date': opportunity.peak_profit_date.isoformat() if opportunity.peak_profit_date else None,
        'peak_profit_percent': round(opportunity.peak_profit_percent, 4),
        'trade_score': round(opportunity.trade_score, 4)
    }


def print_opportunity_summary(opportunities: List[TradeOpportunity], symbol: str) -> None:
    """Print a summary of trading opportunities."""
    if not opportunities:
        print(f"❌ No trading opportunities found for {symbol}")
        return

    print(f"\n🎯 Top Trading Opportunities for {symbol}")
    print("=" * 80)

    total_profit = sum(opp.profit_percent for opp in opportunities)
    avg_profit = total_profit / len(opportunities)
    avg_holding_days = sum(opp.holding_days for opp in opportunities) / len(opportunities)

    print(f"Total Opportunities: {len(opportunities)}")
    print(f"Average Profit: {avg_profit:.2f}%")
    print(f"Average Holding Period: {avg_holding_days:.1f} days")
    print(f"Best Trade: {opportunities[0].profit_percent:.2f}% in {opportunities[0].holding_days} days")
    print("\nTop 10 Trades:")
    print("-" * 80)

    for i, opp in enumerate(opportunities[:10], 1):
        print(f"{i:2d}. {opp.position_type.upper():<5} "
              f"{opp.entry_date.strftime('%Y-%m-%d')} → {opp.exit_date.strftime('%Y-%m-%d')} "
              f"({opp.holding_days:2d}d) "
              f"${opp.entry_price:7.2f} → ${opp.exit_price:7.2f} "
              f"= {opp.profit_percent:6.2f}% "
              f"(Score: {opp.trade_score:6.1f})")


def save_results(opportunities: List[TradeOpportunity], config: Dict[str, Any], symbol: str) -> None:
    """Save analysis results based on configuration."""
    output_config = config.get('output', {})
    output_format = output_config.get('format', 'json')

    # Convert opportunities to dictionaries
    opportunity_dicts = [opportunity_to_dict(opp) for opp in opportunities]

    # Save to JSON
    if output_format in ['json', 'both']:
        filename = f"trading_opportunities_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = f"/tmp/{filename}"

        output_data = {
            'symbol': symbol,
            'analysis_date': datetime.now().isoformat(),
            'total_opportunities': len(opportunities),
            'config': config,
            'opportunities': opportunity_dicts
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            logging.info(f"✅ Results saved to {filepath}")
        except Exception as e:
            logging.error(f"❌ Error saving JSON results: {e}")

    # Save to database
    if output_config.get('save_to_database', True):
        try:
            data_access = MarketDataAccess()
            table_name = config.get('database', {}).get('results_table', 'trading_opportunities')
            data_access.save_trading_opportunities(opportunity_dicts, table_name)
        except Exception as e:
            logging.error(f"❌ Error saving to database: {e}")


def main():
    """Main analysis function."""
    parser = argparse.ArgumentParser(description='Analyze Trading Opportunities')
    parser.add_argument('--config', type=str, default='config/trading_config.yaml',
                       help='Configuration file path')
    parser.add_argument('--symbols', nargs='+', help='Symbols to analyze (overrides config)')
    parser.add_argument('--top-trades', type=int, help='Number of top trades to return (overrides config)')
    parser.add_argument('--output', choices=['json', 'csv', 'both'], help='Output format (overrides config)')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD, overrides config)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD, overrides config)')
    parser.add_argument('--dry-run', action='store_true', help='Test configuration without analysis')

    args = parser.parse_args()

    try:
        # Load configuration
        config = load_config(args.config)

        # Setup logging
        setup_logging(config)
        logger = logging.getLogger(__name__)

        logger.info("🚀 Starting Trading Opportunity Analysis")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Configuration: {args.config}")

        # Override config with command line arguments
        if args.symbols:
            config['analysis']['symbols'] = args.symbols
        if args.top_trades:
            config['analysis']['top_trades_count'] = args.top_trades
        if args.output:
            config['output']['format'] = args.output
        if args.start_date:
            config['analysis']['start_date'] = args.start_date
        if args.end_date:
            config['analysis']['end_date'] = args.end_date

        symbols = config['analysis']['symbols']
        top_trades_count = config['analysis']['top_trades_count']

        logger.info(f"Symbols to analyze: {symbols}")
        logger.info(f"Top trades per symbol: {top_trades_count}")

        if args.dry_run:
            logger.info("🧪 DRY RUN MODE - Configuration test completed successfully")
            return 0

        # Initialize components
        data_access = MarketDataAccess()
        detector = TradingOpportunityDetector(config)

        # Analyze each symbol
        for symbol in symbols:
            logger.info(f"\n📊 Analyzing {symbol}")

            try:
                # Get date range
                start_date = None
                end_date = None
                if config['analysis'].get('start_date'):
                    start_date = datetime.strptime(config['analysis']['start_date'], '%Y-%m-%d')
                if config['analysis'].get('end_date'):
                    end_date = datetime.strptime(config['analysis']['end_date'], '%Y-%m-%d')

                # Retrieve market data
                price_data = data_access.get_market_data(symbol, start_date, end_date)

                if price_data.empty:
                    logger.warning(f"❌ No data available for {symbol}")
                    continue

                # Analyze opportunities
                opportunities = detector.analyze_symbol(symbol, price_data)

                if opportunities:
                    # Get top opportunities
                    top_opportunities = detector.get_top_opportunities(opportunities, top_trades_count)

                    # Print summary
                    print_opportunity_summary(top_opportunities, symbol)

                    # Save results
                    save_results(top_opportunities, config, symbol)

                    logger.info(f"✅ Analysis completed for {symbol}: {len(top_opportunities)} top opportunities")
                else:
                    logger.warning(f"❌ No profitable opportunities found for {symbol}")

            except Exception as e:
                logger.error(f"❌ Error analyzing {symbol}: {e}")
                continue

        logger.info("🎉 Trading opportunity analysis completed!")
        return 0

    except KeyboardInterrupt:
        logger.info("🛑 Analysis interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"💥 Fatal error in trading analysis: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)