FROM python:3.11-slim

# Install system dependencies for pyswisseph compilation
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    pkg-config \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script
COPY enhanced_hourly_lunar_tester.py .

# Run the enhanced hourly lunar tester
CMD ["python", "/app/enhanced_hourly_lunar_tester.py"]