# How to Run with Yahoo Finance Data

## 🚀 Quick Start (30 seconds)

### 1. Install Dependencies
```bash
pip install yfinance pandas numpy scikit-learn scipy
```

### 2. Run with Any Stock
```bash
# Super simple demo
python quick_start.py

# Detailed analysis
python run_with_yahoo.py
```

That's it! The system will automatically:
- Download real stock data from Yahoo Finance
- Create time series segments
- Generate embeddings
- Show similarity analysis

## 📊 What You Get

### Sample Output:
```
📈 Quick Demo with AAPL
========================================
1. Downloading data...
   Got 126 trading days
2. Loading with TimeSeriesLoader...
   Shape: (126, 7)
3. Creating segments...
   Created 59 segments
4. Generating embeddings...
   Embeddings shape: (59, 10)
5. Results:
   First segment: 2025-04-11 to 2025-04-25
   Price range: $192.69 - $208.77
   Price change: 5.62%

✅ Done! Ready to build vector index with 59 segments
```

## 📁 Using Your Own CSV Files

### Yahoo Finance CSV Format:
```python
from tsindexing.data.loader import TimeSeriesLoader

loader = TimeSeriesLoader()
df = loader.load_csv("AAPL.csv", date_column="Date")
segments = loader.create_segments(df, window_size=20, stride=5)
```

### Any CSV Format:
```python
# Custom format: timestamp,price,volume,symbol
df = loader.load_csv(
    "your_data.csv",
    date_column="timestamp",
    value_columns=["price", "volume"],
    symbol_column="symbol"
)
```

## 🔧 Customization

### Change Stock Symbol:
Edit `quick_start.py` and change:
```python
symbols = ["AAPL", "GOOGL", "TSLA"]  # Add any valid ticker
```

### Adjust Window Size:
```python
segments = loader.create_segments(
    df,
    window_size=30,  # 30-day windows (6 weeks)
    stride=5,        # 5-day stride (weekly updates)
    value_columns=["Close", "Volume"]
)
```

### Embedding Settings:
```python
encoder = FeatureEncoder(
    use_fft=True,           # Frequency features
    fft_components=10,      # Number of FFT components
    use_statistical=True,   # Statistical features
    pca_components=15,      # Dimensionality
    normalize=True          # Standardize features
)
```

## 📈 Next Steps

After running successfully, you can:

1. **Build Vector Index**: Use the segments and embeddings with IndexBuilder
2. **Query Similar Patterns**: Find historically similar market conditions
3. **Add Text Context**: Include news/events for each time period
4. **Scale Up**: Process multiple stocks, longer time periods

## 🛠️ Troubleshooting

### Common Issues:

**"ModuleNotFoundError: No module named 'yfinance'"**
```bash
pip install yfinance
```

**"No data found for symbol"**
- Check if symbol is valid (e.g., "AAPL", not "Apple")
- Try a different time period

**"Empty segments created"**
- Reduce window_size (try 10 instead of 30)
- Check if CSV has enough data

### Getting Help:
- Check the sample files in `data/` directory
- Run `python examples/test_with_sample_data.py` for offline testing
- See `DATA_SOURCES.md` for more data source options

## ✅ Success Indicators

You'll know it's working when you see:
- ✅ Data downloaded successfully
- ✅ Segments created (>0 number)
- ✅ Embeddings generated with expected shape
- ✅ No error messages

The system is now ready for building a complete RAG indexing pipeline!