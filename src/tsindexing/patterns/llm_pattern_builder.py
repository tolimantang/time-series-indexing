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
""",

            "low_volatility": """
List dates from 2000-2024 when markets showed very low volatility.
Include periods when VIX was consistently below 15 and markets were calm.

Format: YYYY-MM-DD (one per line)

Include periods of:
- VIX <15 for extended periods
- Calm, steady market conditions
- Low daily price movements
- "Goldilocks" economic periods

Output only the dates, no explanations:
""",

            "bull_market_steady": """
List dates from 2000-2024 during steady bull market climbs.
Include periods of gradual, consistent upward market movement.

Format: YYYY-MM-DD (one per line)

Include periods of:
- Steady upward trends without major corrections
- Gradual price appreciation over weeks/months
- Calm but positive market sentiment
- Recovery periods with consistent gains

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
            ],

            "low_volatility": [
                # 2017 - Famous low VIX year
                "2017-01-03", "2017-02-15", "2017-04-10", "2017-05-08",
                "2017-07-10", "2017-09-05", "2017-11-15",

                # 2014-2015 calm periods
                "2014-03-15", "2014-06-20", "2014-09-10", "2014-11-25",
                "2015-02-10", "2015-05-15", "2015-07-20",

                # 2012-2013 recovery periods
                "2012-03-20", "2012-07-15", "2012-09-25", "2012-11-30",
                "2013-01-15", "2013-04-25", "2013-08-10", "2013-10-15",

                # 2006-2007 pre-crisis calm
                "2006-08-15", "2006-10-20", "2007-01-10", "2007-04-15",
                "2007-06-25", "2007-08-01",

                # 2004-2005 steady periods
                "2004-03-15", "2004-07-20", "2005-04-15", "2005-07-25"
            ],

            "bull_market_steady": [
                # 2013-2015 steady climb post-QE
                "2013-02-20", "2013-05-15", "2013-08-05", "2013-10-25",
                "2014-01-15", "2014-04-10", "2014-07-15", "2014-10-05",
                "2015-01-20", "2015-04-15",

                # 2016-2017 Trump rally
                "2016-11-15", "2016-12-20", "2017-01-25", "2017-03-15",
                "2017-05-10", "2017-07-25", "2017-09-15", "2017-11-05",

                # 2009-2011 recovery climb
                "2009-05-15", "2009-08-20", "2009-11-10", "2010-02-25",
                "2010-07-15", "2010-09-20", "2011-01-15", "2011-04-25",

                # 2003-2006 steady bull
                "2003-05-15", "2003-09-10", "2004-01-20", "2004-05-25",
                "2005-01-10", "2005-08-15", "2006-02-15", "2006-05-20"
            ]
        }

        if pattern_type not in curated_patterns:
            raise ValueError(f"Unknown pattern type: {pattern_type}. "
                           f"Available: {list(curated_patterns.keys())}")

        print(f"Using curated {pattern_type} dates (replace with LLM call)")
        print(f"LLM Prompt would be:\n{self.llm_prompts[pattern_type]}")

        return curated_patterns[pattern_type]

    def get_market_data_for_dates(self, dates: List[str], asset: str = "SPY",
                                 window_days: int = 512) -> List[Dict]:
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
                end_date = start_date + timedelta(days=window_days + 200)  # Much larger buffer for 512 days

                # Get data
                ticker = yf.Ticker(asset)
                data = ticker.history(start=start_date, end=end_date)

                if len(data) < window_days // 4:  # Must have at least quarter the data
                    print(f"  ⚠️  {date_str}: Insufficient data ({len(data)} days)")
                    continue

                # Take first window_days of data, pad if necessary
                if len(data) >= window_days:
                    segment_data = data.head(window_days)
                else:
                    # Pad with last values if insufficient data
                    segment_data = data.copy()
                    last_row = data.iloc[-1:].copy()
                    for _ in range(window_days - len(data)):
                        segment_data = pd.concat([segment_data, last_row], ignore_index=True)

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
        """Create average PatchTST embedding from segments using pre-trained model.

        Args:
            segments: List of market data segments

        Returns:
            Average embedding vector
        """
        try:
            # Import PatchTST from HuggingFace
            from transformers import PatchTSTModel
            import torch

            # Better device selection for MacOS compatibility
            if torch.backends.mps.is_available():
                device = "mps"
                dtype = torch.float32  # MPS doesn't support bfloat16
                print("Using MPS (Apple Silicon) with float32")
            elif torch.cuda.is_available():
                device = "cuda"
                dtype = torch.float32
                print("Using CUDA with float32")
            else:
                device = "cpu"
                dtype = torch.float32
                print("Using CPU with float32")

            print("Loading pre-trained PatchTST model...")
            # Use IBM's pre-trained model
            model = PatchTSTModel.from_pretrained("ibm-granite/granite-timeseries-patchtst").to(device).eval()
            config = model.config

            print(f"Model config: context_length={config.context_length}, channels={config.num_input_channels}")

            embeddings = []
            print(f"Creating embeddings for {len(segments)} segments...")

            for i, segment in enumerate(segments):
                # Get both Close and Volume (we need 7 channels but only have 2)
                close_prices = segment["values"][:, 0]
                volume = segment["values"][:, 1]

                # Normalize volume to same scale as prices (rough approximation)
                volume_normalized = volume / np.mean(volume) * np.mean(close_prices)

                # Create 7 channels by repeating and transforming our data
                # This is a hack to match the pre-trained model's expected input
                channel_data = []
                channel_data.append(close_prices)  # Original close
                channel_data.append(volume_normalized)  # Normalized volume
                channel_data.append(np.diff(close_prices, prepend=close_prices[0]))  # Price changes
                channel_data.append(np.cumsum(close_prices - close_prices[0]))  # Cumulative changes
                channel_data.append(np.log(close_prices / close_prices[0] + 1e-8))  # Log returns
                channel_data.append(np.roll(close_prices, 1))  # Lagged prices
                channel_data.append(close_prices - np.mean(close_prices))  # Mean-centered prices

                # Stack into [context_length, num_channels] format
                # Ensure we have exactly context_length points
                target_length = config.context_length  # Use full 512 length

                multi_channel_data = []
                for channel in channel_data:
                    if len(channel) >= target_length:
                        # Take last target_length points
                        channel_trimmed = channel[-target_length:]
                    else:
                        # Pad with last value if too short
                        padding = [channel[-1]] * (target_length - len(channel))
                        channel_trimmed = np.concatenate([channel, padding])
                    multi_channel_data.append(channel_trimmed)

                # Shape: [context_length, num_channels]
                ts_array = np.array(multi_channel_data).T

                # Convert to tensor: [batch_size, context_length, num_channels]
                ts_tensor = torch.tensor(ts_array, dtype=dtype, device=device).unsqueeze(0)

                # Debug tensor shape
                if i == 0:  # Only print for first segment
                    print(f"  Debug: ts_tensor shape: {ts_tensor.shape}")
                    print(f"  Debug: Expected shape: [1, {target_length}, 7]")

                with torch.no_grad():
                    # Get model outputs (we want the hidden states for embeddings)
                    outputs = model(ts_tensor, output_hidden_states=True)

                    # Extract embedding from last hidden state
                    # outputs.last_hidden_state shape: [batch_size, num_patches, d_model]
                    hidden_state = outputs.last_hidden_state.squeeze(0)  # Remove batch dim

                    # Pool across patches to get fixed-size embedding
                    embedding = torch.mean(hidden_state, dim=0)  # [d_model]

                    embeddings.append(embedding.cpu().numpy())

                if (i + 1) % 5 == 0:
                    print(f"  Progress: {i + 1}/{len(segments)}")

            # Debug: Check embedding shapes
            shapes = [emb.shape for emb in embeddings]
            print(f"  Debug: Embedding shapes: {shapes[:5]}...")  # Show first 5

            # Average all embeddings and ensure we get a 1D vector
            avg_embedding = np.mean(embeddings, axis=0)

            # Flatten if needed to get 1D embedding
            if avg_embedding.ndim > 1:
                avg_embedding = avg_embedding.flatten()

            print(f"  ✅ Created average embedding with shape: {avg_embedding.shape}")

            return avg_embedding

        except ImportError as e:
            print(f"❌ PatchTST not installed: {e}")
            print("Install with: pip install transformers")
            # Return dummy embedding for testing
            return np.random.randn(128)
        except Exception as e:
            print(f"❌ Error creating embeddings: {e}")
            import traceback
            traceback.print_exc()
            return np.random.randn(128)

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

        for pattern_type in ["fed_rate_hikes", "market_crashes", "vix_spikes", "low_volatility", "bull_market_steady"]:
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