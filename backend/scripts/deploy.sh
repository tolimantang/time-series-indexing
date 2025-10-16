#!/bin/bash

# Deployment script for Market Encoder to EKS
set -e

# Configuration
DOCKER_IMAGE="market-encoder:latest"
ECR_REPO="your-account.dkr.ecr.region.amazonaws.com/market-encoder"
KUBE_NAMESPACE="time-series-indexing"

echo "🚀 Deploying Market Encoder to EKS"

# Build Docker image
echo "📦 Building Docker image..."
cd "$(dirname "$0")/.."
docker build -f Dockerfile.market-encoder -t $DOCKER_IMAGE .

# Tag for ECR (update with your ECR repository)
echo "🏷️  Tagging image for ECR..."
docker tag $DOCKER_IMAGE $ECR_REPO:latest
docker tag $DOCKER_IMAGE $ECR_REPO:$(date +%Y%m%d-%H%M%S)

# Push to ECR (uncomment when ready)
echo "⬆️  Pushing to ECR..."
echo "# aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin $ECR_REPO"
echo "# docker push $ECR_REPO:latest"
echo "# docker push $ECR_REPO:$(date +%Y%m%d-%H%M%S)"

# Apply Kubernetes manifests
echo "☸️  Applying Kubernetes manifests..."

# Create namespace if it doesn't exist
kubectl apply -f k8s/namespace.yaml

# Apply deployment and services
kubectl apply -f k8s/market-encoder-deployment.yaml

# Apply CronJob for daily updates
kubectl apply -f k8s/market-encoder-cronjob.yaml

echo "✅ Deployment complete!"

# Show status
echo "📊 Checking deployment status..."
kubectl get pods -n $KUBE_NAMESPACE -l app=market-encoder
kubectl get pvc -n $KUBE_NAMESPACE
kubectl get cronjobs -n $KUBE_NAMESPACE

echo ""
echo "🔍 To check logs:"
echo "kubectl logs -n $KUBE_NAMESPACE -l app=market-encoder --follow"
echo ""
echo "🧪 To run a test job:"
echo "kubectl create job --from=cronjob/market-encoder-daily test-run -n $KUBE_NAMESPACE"