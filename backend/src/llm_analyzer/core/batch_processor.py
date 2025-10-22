"""
Batch processor for analyzing large datasets of trading opportunities.
Handles memory management and API rate limiting for Claude analysis.
"""

import logging
import time
import json
import psycopg2
from typing import List, Dict, Any, Optional
from datetime import datetime
from .data_retriever import TradingDataRetriever
from .claude_analyzer import ClaudeAnalyzer
from ..models.trading_data import TradingOpportunity

logger = logging.getLogger(__name__)


class BatchAstroProcessor:
    """Processes trading opportunities in batches for scalable analysis."""

    def __init__(self, batch_size: int = 50, delay_between_batches: float = 5.0):
        """
        Initialize batch processor.

        Args:
            batch_size: Number of opportunities to process per batch
            delay_between_batches: Seconds to wait between batches (API rate limiting)
        """
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.data_retriever = TradingDataRetriever()
        self.claude_analyzer = ClaudeAnalyzer()

    def process_all_opportunities(self, min_astro_score: Optional[float] = None) -> Dict[str, Any]:
        """
        Process all trading opportunities in batches.

        Args:
            min_astro_score: Minimum astrological score to include

        Returns:
            Summary of processing results
        """
        logger.info("🚀 Starting batch processing of all trading opportunities")

        # Get all opportunities
        opportunities = self.data_retriever.get_all_trading_opportunities()

        if min_astro_score is not None:
            opportunities = [opp for opp in opportunities if opp.astrological_score >= min_astro_score]
            logger.info(f"📊 Filtered to {len(opportunities)} opportunities with astro score >= {min_astro_score}")

        if not opportunities:
            return {"error": "No trading opportunities found"}

        # Process in batches
        total_batches = (len(opportunities) + self.batch_size - 1) // self.batch_size
        processed_count = 0
        insights_extracted = []

        logger.info(f"📦 Processing {len(opportunities)} opportunities in {total_batches} batches of {self.batch_size}")

        for batch_num in range(total_batches):
            start_idx = batch_num * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(opportunities))
            batch = opportunities[start_idx:end_idx]

            logger.info(f"🔄 Processing batch {batch_num + 1}/{total_batches} ({len(batch)} opportunities)")

            try:
                # Analyze batch with Claude
                batch_analysis = self.claude_analyzer.analyze_oil_trading_patterns(batch)

                # Extract structured insights
                batch_insights = self.extract_insights_from_analysis(batch_analysis, batch)

                # Store insights in database
                stored_count = self.store_insights_in_database(batch_insights)

                insights_extracted.extend(batch_insights)
                processed_count += len(batch)

                logger.info(f"✅ Batch {batch_num + 1} completed: {len(batch)} analyzed, {stored_count} insights stored")

                # Delay between batches to respect API limits
                if batch_num < total_batches - 1:  # Don't delay after last batch
                    logger.info(f"⏳ Waiting {self.delay_between_batches}s before next batch...")
                    time.sleep(self.delay_between_batches)

            except Exception as e:
                logger.error(f"❌ Error processing batch {batch_num + 1}: {e}")
                continue

        summary = {
            "total_opportunities": len(opportunities),
            "batches_processed": total_batches,
            "opportunities_analyzed": processed_count,
            "insights_extracted": len(insights_extracted),
            "batch_size": self.batch_size,
            "processing_time": datetime.now().isoformat()
        }

        logger.info(f"🎯 Batch processing completed: {processed_count}/{len(opportunities)} opportunities analyzed")
        return summary

    def extract_insights_from_analysis(self, claude_response: str, batch: List[TradingOpportunity]) -> List[Dict[str, Any]]:
        """
        Parse Claude response into structured insights.

        Args:
            claude_response: Raw response from Claude
            batch: Trading opportunities that were analyzed

        Returns:
            List of structured insights
        """
        insights = []

        try:
            # Parse Claude response for patterns
            # This is a simplified extraction - could be enhanced with NLP
            lines = claude_response.split('\n')
            current_insight = {}

            for line in lines:
                line = line.strip()

                # Look for pattern indicators
                if any(keyword in line.lower() for keyword in ['lunar phase', 'moon', 'phase']):
                    if current_insight:
                        insights.append(current_insight)
                    current_insight = {
                        'insight_type': 'pattern',
                        'category': 'lunar_phase',
                        'pattern_name': line[:100],
                        'description': line,
                        'evidence': {'batch_size': len(batch), 'source': 'claude_batch_analysis'},
                        'claude_analysis': claude_response[:1000] + '...' if len(claude_response) > 1000 else claude_response
                    }

                elif any(keyword in line.lower() for keyword in ['mars', 'jupiter', 'saturn', 'aspect', 'trine', 'square']):
                    if current_insight and current_insight.get('category') != 'planetary_aspect':
                        insights.append(current_insight)
                    current_insight = {
                        'insight_type': 'pattern',
                        'category': 'planetary_aspect',
                        'pattern_name': line[:100],
                        'description': line,
                        'evidence': {'batch_size': len(batch), 'source': 'claude_batch_analysis'},
                        'claude_analysis': claude_response[:1000] + '...' if len(claude_response) > 1000 else claude_response
                    }

                elif any(keyword in line.lower() for keyword in ['seasonal', 'zodiac', 'sign']):
                    if current_insight and current_insight.get('category') != 'seasonal':
                        insights.append(current_insight)
                    current_insight = {
                        'insight_type': 'pattern',
                        'category': 'seasonal',
                        'pattern_name': line[:100],
                        'description': line,
                        'evidence': {'batch_size': len(batch), 'source': 'claude_batch_analysis'},
                        'claude_analysis': claude_response[:1000] + '...' if len(claude_response) > 1000 else claude_response
                    }

                # Look for trading rules
                elif any(keyword in line.lower() for keyword in ['enter', 'exit', 'buy', 'sell', 'trade']):
                    insights.append({
                        'insight_type': 'rule',
                        'category': 'trading_action',
                        'pattern_name': line[:100],
                        'description': line,
                        'evidence': {'batch_size': len(batch), 'source': 'claude_batch_analysis'},
                        'claude_analysis': claude_response[:500] + '...' if len(claude_response) > 500 else claude_response
                    })

            # Add final insight if exists
            if current_insight:
                insights.append(current_insight)

            # Calculate basic statistics for insights
            avg_profit = sum(opp.profit_percent for opp in batch) / len(batch)
            avg_astro_score = sum(opp.astrological_score for opp in batch) / len(batch)

            # Add batch statistics to insights
            for insight in insights:
                insight.update({
                    'confidence_score': avg_astro_score,
                    'avg_profit': avg_profit,
                    'trade_count': len(batch)
                })

            logger.info(f"📊 Extracted {len(insights)} insights from Claude response")
            return insights

        except Exception as e:
            logger.error(f"❌ Error extracting insights: {e}")
            return []

    def store_insights_in_database(self, insights: List[Dict[str, Any]]) -> int:
        """
        Store extracted insights in astrological_insights table.

        Args:
            insights: List of structured insights

        Returns:
            Number of insights successfully stored
        """
        if not insights:
            return 0

        try:
            conn = psycopg2.connect(**self.data_retriever.db_config)
            cursor = conn.cursor()

            stored_count = 0

            for insight in insights:
                try:
                    cursor.execute("""
                        INSERT INTO astrological_insights (
                            insight_type, category, pattern_name, description,
                            confidence_score, avg_profit, trade_count, evidence, claude_analysis
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        insight.get('insight_type'),
                        insight.get('category'),
                        insight.get('pattern_name'),
                        insight.get('description'),
                        insight.get('confidence_score'),
                        insight.get('avg_profit'),
                        insight.get('trade_count'),
                        json.dumps(insight.get('evidence', {})),
                        insight.get('claude_analysis')
                    ))
                    stored_count += 1

                except Exception as e:
                    logger.warning(f"⚠️ Failed to store insight: {e}")
                    continue

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"💾 Stored {stored_count}/{len(insights)} insights in database")
            return stored_count

        except Exception as e:
            logger.error(f"❌ Database error storing insights: {e}")
            return 0

    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status from database."""
        try:
            conn = psycopg2.connect(**self.data_retriever.db_config)
            cursor = conn.cursor()

            # Count total opportunities
            cursor.execute("SELECT COUNT(*) FROM trading_opportunities WHERE astro_analyzed_at IS NOT NULL")
            total_opportunities = cursor.fetchone()[0]

            # Count stored insights
            cursor.execute("SELECT COUNT(*) FROM astrological_insights")
            total_insights = cursor.fetchone()[0]

            # Get latest insight
            cursor.execute("SELECT created_at FROM astrological_insights ORDER BY created_at DESC LIMIT 1")
            latest_insight = cursor.fetchone()

            cursor.close()
            conn.close()

            return {
                "total_opportunities": total_opportunities,
                "total_insights": total_insights,
                "latest_insight": latest_insight[0] if latest_insight else None,
                "insights_per_opportunity": total_insights / total_opportunities if total_opportunities > 0 else 0
            }

        except Exception as e:
            logger.error(f"❌ Error getting processing status: {e}")
            return {"error": str(e)}