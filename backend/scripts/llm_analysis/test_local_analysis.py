#!/usr/bin/env python3
"""
Test the LLM analyzer system locally without Claude API.
"""

import os
import sys
import logging
from pathlib import Path

# Add backend/src to path for imports
backend_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(backend_src))

from llm_analyzer.core.data_retriever import TradingDataRetriever
from llm_analyzer.prompts.oil_trading_prompts import OilTradingPrompts

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_data_retrieval():
    """Test data retrieval from database."""
    try:
        logger.info("🧪 Testing data retrieval...")
        retriever = TradingDataRetriever()

        opportunities = retriever.get_all_trading_opportunities()
        logger.info(f"✅ Retrieved {len(opportunities)} trading opportunities")

        if opportunities:
            sample = opportunities[0]
            logger.info(f"📊 Sample trade: {sample.symbol} {sample.position_type} - {sample.profit_percent:.1f}% profit")
            logger.info(f"⭐ Astrological score: {sample.astrological_score}/100")

        stats = retriever.get_trading_statistics()
        logger.info(f"📈 Dataset stats: {stats['total_trades']} trades, avg profit: {stats['avg_profit']:.1f}%")

        return opportunities

    except Exception as e:
        logger.error(f"❌ Data retrieval test failed: {e}")
        return None


def test_prompt_generation(opportunities):
    """Test prompt generation."""
    try:
        logger.info("🧪 Testing prompt generation...")

        # Test comprehensive prompt
        comprehensive_prompt = OilTradingPrompts.generate_comprehensive_oil_analysis_prompt(opportunities)
        logger.info(f"✅ Generated comprehensive prompt: {len(comprehensive_prompt)} characters")

        # Test lunar phase prompt
        lunar_prompt = OilTradingPrompts.generate_lunar_phase_analysis_prompt(opportunities)
        logger.info(f"✅ Generated lunar phase prompt: {len(lunar_prompt)} characters")

        # Test planetary aspects prompt
        aspects_prompt = OilTradingPrompts.generate_planetary_aspects_prompt(opportunities)
        logger.info(f"✅ Generated planetary aspects prompt: {len(aspects_prompt)} characters")

        return comprehensive_prompt

    except Exception as e:
        logger.error(f"❌ Prompt generation test failed: {e}")
        return None


def main():
    """Main test function."""
    logger.info("🧪 Testing LLM Analyzer System Locally")

    # Test data retrieval
    opportunities = test_data_retrieval()
    if not opportunities:
        logger.error("❌ Cannot proceed without trading data")
        return 1

    # Test prompt generation
    prompt = test_prompt_generation(opportunities)
    if not prompt:
        logger.error("❌ Prompt generation failed")
        return 1

    # Display sample results
    print("\n" + "="*80)
    print("🧪 LLM ANALYZER LOCAL TEST RESULTS")
    print("="*80)
    print(f"✅ Data Retrieval: {len(opportunities)} trading opportunities loaded")
    print(f"✅ Prompt Generation: {len(prompt)} character comprehensive prompt created")
    print(f"✅ System Ready: All components working correctly")

    print(f"\n📊 Dataset Summary:")
    print(f"- Total Trades: {len(opportunities)}")
    print(f"- Long Positions: {len([o for o in opportunities if o.position_type == 'long'])}")
    print(f"- Short Positions: {len([o for o in opportunities if o.position_type == 'short'])}")
    print(f"- Average Profit: {sum(o.profit_percent for o in opportunities) / len(opportunities):.1f}%")
    print(f"- Average Astrological Score: {sum(o.astrological_score for o in opportunities) / len(opportunities):.1f}/100")

    print(f"\n🎯 Ready for Claude Analysis!")
    print(f"To run with Claude API:")
    print(f"1. Set ANTHROPIC_API_KEY environment variable")
    print(f"2. Run: python3 scripts/llm_analysis/run_oil_astro_analysis.py --analysis-type comprehensive")
    print(f"3. Or deploy: kubectl apply -f deploy/k8s/shared/claude-oil-analysis-job.yaml")

    print("\n📋 Sample Prompt Preview (first 500 chars):")
    print("-" * 80)
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print("="*80)

    logger.info("✅ Local test completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())