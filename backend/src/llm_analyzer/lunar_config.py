"""
Configuration for Lunar Pattern Testing
"""

import os
from datetime import datetime, timedelta

# Database configuration (reads from environment variables)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'financial_postgres'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

# Market configuration
MARKET_CONFIG = {
    'oil': {
        'symbol': 'CL',
        'name': 'Crude Oil',
        'price_table': 'oil_prices',  # Table name where price data is stored
        'price_column': 'close_price',
        'date_column': 'trade_date'
    },
    'gold': {
        'symbol': 'GC',
        'name': 'Gold',
        'price_table': 'gold_prices',
        'price_column': 'close_price',
        'date_column': 'trade_date'
    },
    'spx': {
        'symbol': 'ES',
        'name': 'S&P 500',
        'price_table': 'spx_prices',
        'price_column': 'close_price',
        'date_column': 'trade_date'
    }
}

# Testing parameters
TESTING_CONFIG = {
    # Time windows to test market impact (days after lunar event)
    'market_move_windows': [1, 2, 3, 5, 7],

    # Minimum percentage move to be considered significant
    'significance_threshold': 0.5,

    # Required consistency rate for a pattern to be considered valid
    'pattern_consistency_threshold': 0.65,

    # Minimum number of occurrences required to validate a pattern
    'minimum_occurrences': 3,

    # Maximum orb for lunar aspects (degrees)
    'max_orb_degrees': 3.0,

    # How far back to check for material changes (days)
    'material_change_lookback_days': 90,

    # Minimum significance for material changes
    'material_change_significance_threshold': 0.7,

    # Statistical significance required for pattern validation
    'statistical_significance_threshold': 0.05,
}

# Planets to test lunar aspects against
PLANETS_TO_TEST = [
    'Sun',
    'Mercury',
    'Venus',
    'Mars',
    'Jupiter',
    'Saturn',
    'Uranus',
    'Neptune',
    'Pluto'
]

# Lunar aspect types to test
LUNAR_ASPECTS = [
    'conjunction',  # 0 degrees
    'opposition',   # 180 degrees
    'trine',        # 120 degrees
    'square',       # 90 degrees
    'sextile'       # 60 degrees
]

# Default test periods
DEFAULT_TEST_PERIODS = {
    'short_term': {
        'start': datetime.now() - timedelta(days=2*365),  # 2 years
        'end': datetime.now()
    },
    'medium_term': {
        'start': datetime.now() - timedelta(days=5*365),  # 5 years
        'end': datetime.now()
    },
    'long_term': {
        'start': datetime.now() - timedelta(days=10*365),  # 10 years
        'end': datetime.now()
    }
}

# Output configuration
OUTPUT_CONFIG = {
    'results_directory': '/tmp/lunar_pattern_results',
    'save_detailed_results': True,
    'save_charts': True,
    'save_csv_exports': True
}