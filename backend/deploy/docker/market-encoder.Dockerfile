# Multi-stage Docker build for Market Encoder
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Add PostgreSQL and additional dependencies for market encoder
RUN pip install --no-cache-dir \
    psycopg2-binary \
    pyyaml \
    sentence-transformers \
    chromadb

# Copy application code
COPY market_encoder/ ./market_encoder/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY sql/ ./sql/

# Create data directory for ChromaDB
RUN mkdir -p /data/chroma_market_db

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV CHROMA_DB_PATH=/data/chroma_market_db

# Create non-root user for security
RUN groupadd -r encoder && useradd -r -g encoder encoder
RUN chown -R encoder:encoder /app /data
USER encoder

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from market_encoder.config import MarketEncoderConfig; MarketEncoderConfig()" || exit 1

# Default command for daily cronjob
CMD ["python", "scripts/daily_market_encoding.py"]