#!/usr/bin/env python3
"""
CLI script to run the Market Encoder.
Usage: python run_market_encoder.py [command]

Commands:
  test     - Run test suite
  update   - Run daily update
  query    - Query market conditions
  stats    - Show collection statistics
"""

import sys
import os
import argparse
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from market_encoder.encoder import MarketEncoder

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_test():
    """Run the test suite."""
    from market_encoder.test_encoder import test_market_encoder
    return test_market_encoder()


def run_update():
    """Run daily market data update."""
    encoder = MarketEncoder()
    result = encoder.run_daily_update()
    print(f"Update Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Processed {result['processed_days']} days")
        print(f"Latest date: {result['latest_date']}")
        if result['latest_signals']:
            signals = result['latest_signals']
            print(f"Latest close: ${signals['price']['close']:.2f}")
            print(f"Daily return: {signals['price']['daily_return']:.2f}%")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    return result['status'] == 'success'


def run_query(query_text: str):
    """Query for similar market conditions."""
    encoder = MarketEncoder()
    results = encoder.query_similar_market_conditions(query_text, n_results=5)

    print(f"Query: {query_text}")
    print(f"Found {results['count']} similar conditions:")
    print("-" * 50)

    if results['results'] and results['results']['documents']:
        for i, (doc, meta, distance) in enumerate(zip(
            results['results']['documents'][0],
            results['results']['metadatas'][0],
            results['results']['distances'][0]
        )):
            print(f"{i+1}. Date: {meta['date']}")
            print(f"   Similarity: {1-distance:.3f}")
            print(f"   Close: ${meta['close_price']:.2f}")
            print(f"   Daily Return: {meta['daily_return']:.2f}%")
            print(f"   Description: {doc}")
            print()


def show_stats():
    """Show collection statistics."""
    encoder = MarketEncoder()
    stats = encoder.get_collection_stats()
    print("Collection Statistics:")
    print(f"Total records: {stats.get('total_records', 'Unknown')}")
    print(f"Date range: {stats.get('date_range', 'Unknown')}")
    print(f"Collection: {stats.get('collection_name', 'Unknown')}")


def main():
    parser = argparse.ArgumentParser(description='Market Encoder CLI')
    parser.add_argument('command', choices=['test', 'update', 'query', 'stats'],
                       help='Command to run')
    parser.add_argument('--query-text', '-q', type=str,
                       help='Query text for similar market conditions')

    args = parser.parse_args()

    try:
        if args.command == 'test':
            success = run_test()
            sys.exit(0 if success else 1)

        elif args.command == 'update':
            success = run_update()
            sys.exit(0 if success else 1)

        elif args.command == 'query':
            if not args.query_text:
                print("Error: --query-text required for query command")
                sys.exit(1)
            run_query(args.query_text)

        elif args.command == 'stats':
            show_stats()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()