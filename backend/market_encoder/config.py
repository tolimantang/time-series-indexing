"""
Configuration loader for market encoder.
Loads securities and settings from YAML configuration.
"""

import yaml
import os
from typing import Dict, List, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Configuration for a single security."""

    def __init__(self, config_dict: Dict[str, Any]):
        self.symbol = config_dict['symbol']
        self.name = config_dict['name']
        self.yahoo_symbol = config_dict['yahoo_symbol']
        self.db_symbol = config_dict['db_symbol']
        self.enabled = config_dict.get('enabled', True)

    def __repr__(self):
        return f"SecurityConfig({self.symbol}, enabled={self.enabled})"


class MarketEncoderConfig:
    """Main configuration class for market encoder."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to config file in the same directory structure
            config_path = Path(__file__).parent.parent / "config" / "securities.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Parse securities
        self.indices = self._parse_securities('indices')
        self.etfs = self._parse_securities('etfs')
        self.stocks = self._parse_securities('stocks')
        self.crypto = self._parse_securities('crypto')

        # Parse encoding settings
        self.encoding = self.config.get('encoding', {})
        self.database = self.config.get('database', {})
        self.logging_config = self.config.get('logging', {})

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            raise

    def _parse_securities(self, category: str) -> List[SecurityConfig]:
        """Parse securities from a category."""
        securities_config = self.config.get('securities', {}).get(category, [])
        return [SecurityConfig(sec_config) for sec_config in securities_config]

    def get_enabled_securities(self) -> List[SecurityConfig]:
        """Get all enabled securities across all categories."""
        all_securities = self.indices + self.etfs + self.stocks + self.crypto
        enabled = [sec for sec in all_securities if sec.enabled]

        logger.info(f"Found {len(enabled)} enabled securities out of {len(all_securities)} total")
        return enabled

    def get_securities_by_category(self, category: str) -> List[SecurityConfig]:
        """Get securities by category (indices, etfs, stocks, crypto)."""
        category_map = {
            'indices': self.indices,
            'etfs': self.etfs,
            'stocks': self.stocks,
            'crypto': self.crypto
        }

        return category_map.get(category, [])

    def get_encoding_setting(self, key: str, default=None):
        """Get encoding configuration setting."""
        return self.encoding.get(key, default)

    def get_database_setting(self, db_type: str, key: str, default=None):
        """Get database configuration setting."""
        return self.database.get(db_type, {}).get(key, default)

    def setup_logging(self):
        """Setup logging based on configuration."""
        log_level = self.logging_config.get('level', 'INFO')
        log_format = self.logging_config.get('format',
                                           '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            force=True
        )

        logger.info(f"Logging configured: level={log_level}")

    def summary(self) -> Dict[str, Any]:
        """Get configuration summary."""
        enabled_securities = self.get_enabled_securities()

        return {
            'total_securities': len(self.indices + self.etfs + self.stocks + self.crypto),
            'enabled_securities': len(enabled_securities),
            'enabled_by_category': {
                'indices': len([s for s in self.indices if s.enabled]),
                'etfs': len([s for s in self.etfs if s.enabled]),
                'stocks': len([s for s in self.stocks if s.enabled]),
                'crypto': len([s for s in self.crypto if s.enabled])
            },
            'encoding_settings': self.encoding,
            'config_path': str(self.config_path)
        }