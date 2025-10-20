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

# Add PostgreSQL dependencies for market encoder (minimal)
RUN pip install --no-cache-dir \
    psycopg2-binary \
    pyyaml

# Copy application code with new src/ layout
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY sql/ ./sql/

# Set environment variables (no ChromaDB needed for simple version)
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN groupadd -r encoder && useradd -r -g encoder encoder
RUN chown -R encoder:encoder /app
USER encoder

# Health check - minimal version
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import psycopg2; print('OK')" || exit 1

# Default command for simple daily cronjob
CMD ["python", "scripts/simple_daily_encoding.py", "--config", "/app/config/securities_simple.yaml"]