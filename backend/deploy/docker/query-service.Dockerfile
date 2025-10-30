# Multi-stage build for Financial Query Service
FROM 928440193005.dkr.ecr.us-west-1.amazonaws.com/astrofinancial-base:latest

# Set service-specific environment variables
ENV PORT=8003
ENV SERVICE_NAME=query-service

# Expose port
EXPOSE 8003

# Add service-specific Python path
ENV PYTHONPATH=/app/src

# Install additional dependencies if needed
# (FastAPI and other dependencies should already be in base image)

# Copy service-specific files if any
# COPY src/query/ /app/src/query/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8003/health || exit 1

# Run the query service
CMD ["python", "-m", "uvicorn", "query.financial_server.api_server:app", "--host", "0.0.0.0", "--port", "8003", "--log-level", "info"]