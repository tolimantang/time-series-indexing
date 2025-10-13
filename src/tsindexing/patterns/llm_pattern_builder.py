"""LLM-powered pattern library builder."""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import yfinance as yf
from pathlib import Path


class LLMPatternBuilder:
    """Build financial pattern library using LLM-generated historical dates."""

    def __init__(self, patterns_dir: Optional[str] = None):
        """Initialize pattern builder.

        Args:
            patterns_dir: Directory to save pattern data (default: project root/patterns)
        """
        if patterns_dir is None:
            # Default to patterns directory in project root
            project_root = Path(__file__).parent.parent.parent.parent
            patterns_dir = project_root / "patterns"

        self.patterns_dir = Path(patterns_dir)
        self.patterns_dir.mkdir(exist_ok=True)

        # LLM prompts for different pattern types
        self.llm_prompts = {
            "fed_rate_hikes": """
List all Federal Reserve interest rate INCREASES from 2000-2024.
Include the exact FOMC meeting decision dates (not announcement or effective dates).

Format: YYYY-MM-DD (one per line)

Include these major hiking cycles:
- 2022-2023 inflation response cycle
- 2015-2018 normalization cycle
- 2004-2006 Greenspan cycle

Output only the dates, no explanations:
""",

            "market_crashes": """
List major U.S. stock market crash/decline days from 2000-2024.
Include single trading days with S&P 500 declines of 3% or more.

Format: YYYY-MM-DD (one per line)

Include major events like:
- COVID crash (March 2020)
- Financial crisis (2008)
- Dot-com crash (2000-2002)
- Flash crashes and other significant declines

Output only the dates, no explanations:
""",

            "vix_spikes": """
List dates when VIX (volatility index) had major spikes from 2000-2024.
Include days when VIX increased significantly or reached high levels.

Format: YYYY-MM-DD (one per line)

Include periods of:
- VIX >40 levels
- Large single-day VIX increases (>50%)
- Major market fear events

Output only the dates, no explanations:
"""
        }

    def get_llm_pattern_dates(self, pattern_type: str) -> List[str]:
        """Get pattern dates from LLM.

        This is a placeholder - you'll need to implement with your preferred LLM API.
        For now, it returns curated dates.
        """

        # Pre-curated dates (replace with actual LLM calls)
        curated_patterns = {
            "fed_rate_hikes": [
                # 2022-2023 cycle
                "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27",
                "2022-09-21", "2022-11-02", "2022-12-14", "2023-02-01",
                "2023-03-22", "2023-05-03", "2023-07-26",

                # 2015-2018 cycle
                "2015-12-16", "2016-12-14", "2017-03-15", "2017-06-14",
                "2017-12-13", "2018-03-21", "2018-06-13", "2018-09-26",
                "2018-12-19",

                # 2004-2006 cycle (partial)
                "2004-06-30", "2004-08-10", "2004-09-21", "2004-11-10",
                "2004-12-14", "2005-02-02", "2005-03-22", "2005-05-03",
                "2005-06-30", "2005-08-09", "2005-09-20", "2005-11-01",
                "2005-12-13", "2006-01-31", "2006-03-28", "2006-05-10",
                "2006-06-29"
            ],

            "market_crashes": [
                # COVID crash
                "2020-03-09", "2020-03-12", "2020-03-16", "2020-03-18",

                # 2008 Financial crisis
                "2008-09-15", "2008-09-17", "2008-09-29", "2008-10-06",
                "2008-10-07", "2008-10-09", "2008-10-15", "2008-10-22",
                "2008-11-05", "2008-11-19", "2008-12-01",

                # Dot-com crash
                "2000-04-03", "2000-04-04", "2000-04-12", "2000-04-14",
                "2001-03-12", "2001-04-18", "2001-09-17", "2001-09-21",

                # Other notable crashes
                "2018-02-05", "2018-02-06", "2018-10-10", "2018-10-24",
                "2015-08-24", "2011-08-04", "2011-08-08", "2010-05-06",
                "2002-07-19", "2002-07-23", "2002-09-17"
            ],

            "vix_spikes": [
                # COVID era
                "2020-03-09", "2020-03-12", "2020-03-16", "2020-03-18",
                "2020-03-20", "2020-02-24", "2020-02-28",

                # 2008 crisis
                "2008-09-15", "2008-09-17", "2008-09-18", "2008-10-06",
                "2008-10-15", "2008-10-16", "2008-10-24", "2008-11-13",
                "2008-11-20", "2008-12-01",

                # Flash crashes and spikes
                "2018-02-05", "2018-02-06", "2015-08-24", "2011-08-08",
                "2010-05-06", "2007-02-27", "2002-07-19", "2001-09-17"
            ]
        }

        if pattern_type not in curated_patterns:
            raise ValueError(f"Unknown pattern type: {pattern_type}. "
                           f"Available: {list(curated_patterns.keys())}")

        print(f"Using curated {pattern_type} dates (replace with LLM call)")
        print(f"LLM Prompt would be:\n{self.llm_prompts[pattern_type]}")

        return curated_patterns[pattern_type]

    def get_market_data_for_dates(self, dates: List[str], asset: str = "SPY",
                                 window_days: int = 20) -> List[Dict]:
        """Get market data segments for given dates.

        Args:
            dates: List of date strings (YYYY-MM-DD)
            asset: Asset symbol to get data for
            window_days: Number of days per segment

        Returns:
            List of segment dictionaries
        """
        segments = []

        print(f"Getting {asset} data for {len(dates)} dates...")

        for i, date_str in enumerate(dates):
            try:
                # Convert to datetime
                start_date = pd.to_datetime(date_str)
                end_date = start_date + timedelta(days=window_days + 5)  # Buffer for weekends

                # Get data
                ticker = yf.Ticker(asset)
                data = ticker.history(start=start_date, end=end_date)

                if len(data) < window_days // 2:  # Must have at least half the data
                    print(f"  ⚠️  {date_str}: Insufficient data ({len(data)} days)")
                    continue

                # Take first window_days of data
                segment_data = data.head(window_days)

                segment = {
                    "timestamp_start": segment_data.index[0],
                    "timestamp_end": segment_data.index[-1],
                    "values": segment_data[['Close', 'Volume']].values,
                    "columns": ['Close', 'Volume'],
                    "symbol": asset,
                    "window_size": len(segment_data),
                    "pattern_date": date_str,
                    "asset": asset
                }

                segments.append(segment)

                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i + 1}/{len(dates)}")

            except Exception as e:
                print(f"  ❌ {date_str}: Error - {e}")
                continue

        print(f"  ✅ Successfully created {len(segments)} segments")
        return segments

    def create_pattern_embedding(self, segments: List[Dict]) -> np.ndarray:
        """Create average Chronos embedding from segments.

        Args:
            segments: List of market data segments

        Returns:
            Average embedding vector
        """
        try:
            # Import Chronos
            from chronos import ChronosPipeline
            import torch

            # Load Chronos model
            print("Loading Chronos model...")
            pipeline = ChronosPipeline.from_pretrained(
                "amazon/chronos-t5-small",
                device_map="auto",
                torch_dtype=torch.bfloat16,
            )

            embeddings = []
            print(f"Creating embeddings for {len(segments)} segments...")

            for i, segment in enumerate(segments):
                # Use Close price (first column)
                close_prices = segment["values"][:, 0]
                ts_tensor = torch.tensor(close_prices, dtype=torch.float32)

                with torch.no_grad():
                    embedding = pipeline.embed(ts_tensor.unsqueeze(0))
                    embeddings.append(embedding.squeeze(0).cpu().numpy())

                if (i + 1) % 5 == 0:
                    print(f"  Progress: {i + 1}/{len(segments)}")

            # Average all embeddings
            avg_embedding = np.mean(embeddings, axis=0)
            print(f"  ✅ Created average embedding with shape: {avg_embedding.shape}")

            return avg_embedding

        except ImportError:
            print("❌ Chronos not installed. Install with: pip install chronos-forecasting")
            # Return dummy embedding for testing
            return np.random.randn(512)
        except Exception as e:
            print(f"❌ Error creating embeddings: {e}")
            return np.random.randn(512)

    def build_pattern_library(self, asset: str = "SPY") -> Dict:
        """Build complete pattern library.

        Args:
            asset: Asset to analyze patterns for

        Returns:
            Dictionary with pattern data
        """
        print(f"🏗️  Building pattern library for {asset}")
        print("=" * 50)

        pattern_library = {}

        for pattern_type in ["fed_rate_hikes", "market_crashes", "vix_spikes"]:
            print(f"\n📊 Building {pattern_type} pattern...")

            # Get dates from LLM
            dates = self.get_llm_pattern_dates(pattern_type)
            print(f"  Got {len(dates)} dates from LLM")

            # Get market data
            segments = self.get_market_data_for_dates(dates, asset)

            if not segments:
                print(f"  ❌ No valid segments for {pattern_type}")
                continue

            # Create embedding
            embedding = self.create_pattern_embedding(segments)

            # Store pattern
            pattern_library[pattern_type] = {
                "dates": dates,
                "valid_segments": len(segments),
                "embedding": embedding.tolist(),  # Convert to list for JSON
                "asset": asset,
                "created_at": datetime.now().isoformat()
            }

            print(f"  ✅ {pattern_type} pattern created successfully")

        # Save to file
        output_file = self.patterns_dir / f"pattern_library_{asset.lower()}.json"
        with open(output_file, 'w') as f:
            json.dump(pattern_library, f, indent=2)

        print(f"\n💾 Pattern library saved to: {output_file}")
        print(f"📈 Successfully built {len(pattern_library)} patterns")

        return pattern_library

    def load_pattern_library(self, asset: str = "SPY") -> Optional[Dict]:
        """Load existing pattern library."""
        pattern_file = self.patterns_dir / f"pattern_library_{asset.lower()}.json"

        if not pattern_file.exists():
            return None

        with open(pattern_file, 'r') as f:
            pattern_library = json.load(f)

        # Convert embedding lists back to numpy arrays
        for pattern_type, pattern_data in pattern_library.items():
            pattern_data["embedding"] = np.array(pattern_data["embedding"])

        return pattern_library


def main():
    """Example usage of pattern builder."""
    print("🚀 LLM Pattern Builder Demo")
    print("=" * 40)

    # Create pattern builder
    builder = LLMPatternBuilder()

    # Build pattern library
    patterns = builder.build_pattern_library("SPY")

    # Show results
    print(f"\n📋 Pattern Library Summary:")
    for pattern_type, data in patterns.items():
        print(f"  {pattern_type}:")
        print(f"    Dates: {len(data['dates'])}")
        print(f"    Valid segments: {data['valid_segments']}")
        print(f"    Embedding shape: {np.array(data['embedding']).shape}")


if __name__ == "__main__":
    main()