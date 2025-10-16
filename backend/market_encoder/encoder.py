"""
Main Market Encoder Service for S&P 500.
Fetches data, generates signals, creates embeddings, and stores in ChromaDB.
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer

from .data_sources import MarketDataManager
from .signal_generator import MarketSignalGenerator
from .text_generator import MarketTextGenerator

logger = logging.getLogger(__name__)


class MarketEncoder:
    """Main market encoder service for S&P 500 data."""

    def __init__(self,
                 chroma_db_path: str = "./chroma_market_db",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """Initialize the market encoder."""
        self.data_manager = MarketDataManager()
        self.signal_generator = MarketSignalGenerator()
        self.text_generator = MarketTextGenerator()

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name="sp500_market_data",
            metadata={"description": "S&P 500 market data embeddings"}
        )

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)

        logger.info(f"MarketEncoder initialized with ChromaDB at {chroma_db_path}")

    def fetch_sp500_data(self, days_back: int = 365) -> pd.DataFrame:
        """Fetch S&P 500 data using Yahoo Finance."""
        symbol = "^GSPC"  # S&P 500 index symbol for Yahoo Finance

        logger.info(f"Fetching {days_back} days of S&P 500 data")
        data = self.data_manager.get_market_data(symbol)

        if data.empty:
            raise ValueError("Failed to fetch S&P 500 data")

        # Limit to requested time period
        cutoff_date = datetime.now() - timedelta(days=days_back)
        data = data[data.index >= cutoff_date]

        logger.info(f"Retrieved {len(data)} days of S&P 500 data")
        return data

    def process_daily_data(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process daily market data into signals and narratives."""
        processed_data = []

        # Generate comprehensive signals for S&P 500
        symbol = "SPX"  # Use SPX as standardized symbol
        signals = self.signal_generator.generate_comprehensive_signals(symbol, data)

        # Get the last 30 days for individual day processing
        recent_data = data.tail(30).copy()

        # Calculate signals for the full dataset first
        recent_data = self.signal_generator.calculate_returns(recent_data)
        recent_data = self.signal_generator.calculate_volatility(recent_data)
        recent_data = self.signal_generator.calculate_technical_indicators(recent_data)
        recent_data = self.signal_generator.detect_regime(recent_data)

        # Process each day
        for date, row in recent_data.iterrows():
            try:
                # Skip if essential data is missing
                if pd.isna(row['close']) or pd.isna(row['daily_return']):
                    continue

                # Create daily signals dictionary
                daily_signals = {
                    'symbol': symbol,
                    'date': date.strftime('%Y-%m-%d'),
                    'price': {
                        'close': float(row['close']),
                        'daily_return': float(row['daily_return']) * 100,
                        'return_5d': float(row.get('return_5d', 0)) * 100,
                        'return_20d': float(row.get('return_20d', 0)) * 100,
                    },
                    'volatility': {
                        'vol_20d': float(row.get('vol_20d', 15)),
                        'volume_ratio': float(row.get('volume_ratio', 1)),
                    },
                    'technical': {
                        'rsi': float(row.get('rsi', 50)),
                        'price_vs_ma20': float(row.get('price_vs_ma20', 0)),
                        'bb_position': float(row.get('bb_position', 0.5)),
                    },
                    'regime': {
                        'vol_regime': row.get('vol_regime', 'normal_vol'),
                        'trend_regime': row.get('trend_regime', 'sideways'),
                        'momentum_regime': row.get('momentum_regime', 'normal_momentum'),
                    }
                }

                # Generate narrative text
                narrative = self.text_generator.generate_market_narrative(symbol, daily_signals)

                processed_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'signals': daily_signals,
                    'narrative': narrative,
                    'symbol': symbol
                })

            except Exception as e:
                logger.warning(f"Error processing data for {date}: {e}")
                continue

        logger.info(f"Processed {len(processed_data)} days of market data")
        return processed_data

    def store_embeddings(self, processed_data: List[Dict[str, Any]]) -> None:
        """Store market narratives as embeddings in ChromaDB."""
        if not processed_data:
            logger.warning("No processed data to store")
            return

        documents = []
        metadatas = []
        ids = []

        for item in processed_data:
            # Use narrative as the document text
            documents.append(item['narrative'])

            # Create metadata with key market metrics
            signals = item['signals']
            metadata = {
                'date': item['date'],
                'symbol': item['symbol'],
                'close_price': signals['price']['close'],
                'daily_return': signals['price']['daily_return'],
                'volatility': signals['volatility']['vol_20d'],
                'rsi': signals['technical']['rsi'],
                'vol_regime': signals['regime']['vol_regime'],
                'trend_regime': signals['regime']['trend_regime'],
                'timestamp': datetime.strptime(item['date'], '%Y-%m-%d').timestamp()
            }
            metadatas.append(metadata)

            # Create unique ID
            ids.append(f"{item['symbol']}_{item['date']}")

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(documents)} market narratives")
        embeddings = self.embedding_model.encode(documents).tolist()

        # Store in ChromaDB (upsert to handle duplicates)
        self.collection.upsert(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"Stored {len(documents)} market data embeddings in ChromaDB")

    def query_similar_market_conditions(self,
                                      query_text: str,
                                      n_results: int = 5) -> Dict[str, Any]:
        """Query for similar market conditions."""
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )

            return {
                'query': query_text,
                'results': results,
                'count': len(results['documents'][0]) if results['documents'] else 0
            }

        except Exception as e:
            logger.error(f"Error querying market conditions: {e}")
            return {'query': query_text, 'results': None, 'count': 0}

    def run_daily_update(self) -> Dict[str, Any]:
        """Run daily market data update process."""
        try:
            logger.info("Starting daily market data update")

            # Fetch recent S&P 500 data (last 60 days to ensure we have enough for indicators)
            data = self.fetch_sp500_data(days_back=60)

            # Process the data
            processed_data = self.process_daily_data(data)

            # Store embeddings
            self.store_embeddings(processed_data)

            # Get latest signals for summary
            latest_signals = processed_data[-1]['signals'] if processed_data else None

            result = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'processed_days': len(processed_data),
                'latest_date': processed_data[-1]['date'] if processed_data else None,
                'latest_signals': latest_signals
            }

            logger.info(f"Daily update completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Daily update failed: {e}")
            return {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the stored market data."""
        try:
            count = self.collection.count()

            # Get recent data to show date range
            if count > 0:
                recent_results = self.collection.query(
                    query_texts=["recent market data"],
                    n_results=min(count, 10),
                    include=['metadatas']
                )

                if recent_results['metadatas'] and recent_results['metadatas'][0]:
                    dates = [meta['date'] for meta in recent_results['metadatas'][0]]
                    date_range = f"{min(dates)} to {max(dates)}"
                else:
                    date_range = "Unknown"
            else:
                date_range = "No data"

            return {
                'total_records': count,
                'date_range': date_range,
                'collection_name': self.collection.name
            }

        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {'error': str(e)}