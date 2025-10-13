"""Demonstrate why reset_index() is needed with yfinance data."""

import yfinance as yf
import pandas as pd

def demonstrate_reset_index():
    """Show the difference between yfinance data with and without reset_index."""
    print("🔍 Why reset_index() is needed with yfinance data\n")

    # Download data
    print("1. Downloading AAPL data...")
    ticker = yf.Ticker("AAPL")
    data = ticker.history(period="5d")  # Just 5 days for demo

    print("\n📊 BEFORE reset_index():")
    print("=" * 40)
    print(f"Shape: {data.shape}")
    print(f"Index type: {type(data.index)}")
    print(f"Index name: {data.index.name}")
    print(f"Columns: {list(data.columns)}")
    print("\nFirst few rows:")
    print(data.head())

    print(f"\nIndex values:")
    print(data.index)

    # The problem: Date is the INDEX, not a column
    print(f"\n❌ Problem: Can't access 'Date' as a column")
    try:
        print(data['Date'])
    except KeyError as e:
        print(f"   KeyError: {e}")

    print(f"\n❌ When saved to CSV without reset_index:")
    data.to_csv("temp_with_index.csv", index=False)  # index=False loses the dates!
    broken_df = pd.read_csv("temp_with_index.csv")
    print("Broken CSV (no date column):")
    print(broken_df.head())
    print(f"Columns: {list(broken_df.columns)}")

    print("\n🔧 AFTER reset_index():")
    print("=" * 40)
    data_reset = data.reset_index()
    print(f"Shape: {data_reset.shape}")
    print(f"Index type: {type(data_reset.index)}")
    print(f"Columns: {list(data_reset.columns)}")
    print("\nFirst few rows:")
    print(data_reset.head())

    print(f"\n✅ Now we can access 'Date' as a column:")
    print(data_reset['Date'])

    print(f"\n✅ When saved to CSV:")
    data_reset.to_csv("temp_fixed.csv", index=False)
    fixed_df = pd.read_csv("temp_fixed.csv")
    print("Fixed CSV (has date column):")
    print(fixed_df.head())
    print(f"Columns: {list(fixed_df.columns)}")

    # Why this matters for TimeSeriesLoader
    print(f"\n🎯 Why this matters for TimeSeriesLoader:")
    print("=" * 50)

    print("""
TimeSeriesLoader expects date as a COLUMN, not as INDEX:

loader.load_csv("data.csv", date_column="Date")  # Looks for Date column

yfinance returns data with Date as INDEX:
┌─────────────┬───────┬───────┬───────┬───────┬─────────┐
│ Date        │ Open  │ High  │ Low   │ Close │ Volume  │  ← Date is INDEX
├─────────────┼───────┼───────┼───────┼───────┼─────────┤
│ 2023-01-03  │ 130.3 │ 130.9 │ 124.2 │ 125.1 │ 112M    │
└─────────────┴───────┴───────┴───────┴───────┴─────────┘

After reset_index(), Date becomes a column:
┌───┬─────────────┬───────┬───────┬───────┬───────┬─────────┐
│   │ Date        │ Open  │ High  │ Low   │ Close │ Volume  │  ← Date is COLUMN
├───┼─────────────┼───────┼───────┼───────┼───────┼─────────┤
│ 0 │ 2023-01-03  │ 130.3 │ 130.9 │ 124.2 │ 125.1 │ 112M    │
└───┴─────────────┴───────┴───────┴───────┴───────┴─────────┘
    """)

    # Cleanup
    import os
    for file in ["temp_with_index.csv", "temp_fixed.csv"]:
        if os.path.exists(file):
            os.remove(file)

    print("🎯 Summary:")
    print("""
1. yfinance returns DataFrame with Date as INDEX
2. TimeSeriesLoader needs Date as COLUMN
3. reset_index() converts INDEX → COLUMN
4. Without it, we lose the date information when saving to CSV
5. With it, TimeSeriesLoader can properly parse the dates

Essential for the pipeline: yfinance → CSV → TimeSeriesLoader
    """)


if __name__ == "__main__":
    demonstrate_reset_index()