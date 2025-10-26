# Backend Services Docker Deployment

This directory contains the Docker-based deployment setup for the AstroFinancial backend services. The deployment uses proper Docker images with Swiss Ephemeris support instead of ConfigMaps.

## Services

- **Backfill Service** (Port 8001): Handles historical data backfilling with Swiss Ephemeris support
- **Backtesting Service** (Port 8000): Runs backtesting algorithms on historical data
- **Recommendation Service** (Port 8002): Provides trading recommendations based on astrological patterns

## Architecture

### Base Image
- `Dockerfile.base`: Contains common dependencies including Swiss Ephemeris, FastAPI, and system packages
- Used as the foundation for all service images

### Service Images
- `Dockerfile.backfill`: Backfill service container
- `Dockerfile.backtesting`: Backtesting service container
- `Dockerfile.recommendation`: Recommendation service container

## Local Development

### Building Images Locally

```bash
# Build base image
docker build -f docker/Dockerfile.base -t astrofinancial-base:latest .

# Build individual services
docker build -f docker/Dockerfile.backfill -t astrofinancial/backfill-service:latest .
docker build -f docker/Dockerfile.backtesting -t astrofinancial/backtesting-service:latest .
docker build -f docker/Dockerfile.recommendation -t astrofinancial/recommendation-service:latest .

# Or use the build script
chmod +x docker/build.sh
./docker/build.sh
```

### Running with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backfill-service

# Stop services
docker-compose down
```

### Testing Services

```bash
# Test backfill service
curl http://localhost:8001/health

# Test backtesting service
curl http://localhost:8000/health

# Test recommendation service
curl http://localhost:8002/health
```

## Production Deployment

### GitHub Actions CI/CD

The project includes a GitHub Actions workflow (`.github/workflows/deploy-backend-services.yml`) that:

1. **Builds**: Creates Docker images with proper Swiss Ephemeris installation
2. **Pushes**: Uploads images to Amazon ECR
3. **Deploys**: Updates Kubernetes deployments with new image versions
4. **Verifies**: Checks service health and readiness

### Automatic Deployment

Deployments are triggered on:
- Push to `main` branch with changes in `backend/` directory
- Manual workflow dispatch

### ECR Repositories

The workflow automatically creates ECR repositories:
- `astrofinancial-backfill-service`
- `astrofinancial-backtesting-service`
- `astrofinancial-recommendation-service`

### Kubernetes Deployments

Located in `deploy/k8s/services-docker/`:
- `backfill-service.yaml`
- `backtesting-service.yaml`
- `recommendation-service.yaml`

Each deployment includes:
- ECR image references
- Health checks (liveness and readiness probes)
- Resource limits and requests
- Security contexts
- Environment variables from secrets

## Configuration

### Environment Variables

Services use these environment variables:
- `DB_HOST`: Database hostname
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `PYTHONPATH`: Python module path (/app/src)

### Secrets

Database credentials are stored in Kubernetes secrets:
- Secret name: `market-encoder-secrets`
- Keys: `db-host`, `db-user`, `db-name`, `db-password`

## Dependencies

### Python Dependencies (pyproject.toml)

Core dependencies include:
- **FastAPI**: Web framework for REST APIs
- **pyswisseph**: Swiss Ephemeris for astronomical calculations
- **psycopg2-binary**: PostgreSQL database adapter
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing

### System Dependencies

The base image includes:
- Build tools (gcc, g++, make)
- PostgreSQL client libraries
- curl and wget for health checks
- Swiss Ephemeris native libraries

## Health Checks

All services expose health endpoints:
- **Endpoint**: `/health`
- **Method**: GET
- **Response**: JSON status with service name and timestamp

## Monitoring

### Kubernetes Health Checks

- **Liveness Probe**: Checks if service is running (30s intervals)
- **Readiness Probe**: Checks if service is ready to receive traffic (10s intervals)
- **Startup Time**: 15-30s initial delay

### Resource Limits

Each service has:
- **CPU Request**: 250m (0.25 cores)
- **CPU Limit**: 1000m (1 core)
- **Memory Request**: 512Mi
- **Memory Limit**: 2Gi

## Troubleshooting

### Common Issues

1. **Swiss Ephemeris Installation**
   - Ensure build tools are available in base image
   - Check pyswisseph installation in container
   - Verify ephemeris data files are accessible

2. **Database Connection**
   - Check secret values in Kubernetes
   - Verify database hostname and port
   - Test connectivity from pod

3. **Image Pull Errors**
   - Ensure ECR repositories exist
   - Check AWS credentials in GitHub secrets
   - Verify image tags match deployment

### Debugging Commands

```bash
# Check pod status
kubectl get pods -n time-series-indexing

# View pod logs
kubectl logs -f deployment/backfill-service -n time-series-indexing

# Exec into pod
kubectl exec -it deployment/backfill-service -n time-series-indexing -- bash

# Test service connectivity
kubectl port-forward svc/backfill-service 8001:8001 -n time-series-indexing

# Check service configuration
kubectl describe deployment backfill-service -n time-series-indexing
```

## Migration from ConfigMap Deployment

The new Docker-based deployment replaces the previous ConfigMap approach:

### Advantages
- ✅ Proper dependency management with pyproject.toml
- ✅ Swiss Ephemeris installed at build time
- ✅ Faster startup times (no runtime installs)
- ✅ Better security (immutable images)
- ✅ Easier debugging and testing
- ✅ Production-ready deployment pattern

### Migration Steps
1. Build new Docker images
2. Push to ECR via GitHub Actions
3. Apply new Kubernetes deployments
4. Remove old ConfigMap-based deployments

The GitHub Actions workflow handles this migration automatically on push to main.