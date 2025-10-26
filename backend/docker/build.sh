#!/bin/bash

# Build script for astrofinancial services
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="${DOCKER_REGISTRY:-astrofinancial}"
TAG="${DOCKER_TAG:-latest}"
PUSH="${PUSH:-false}"

echo -e "${GREEN}🔨 Building AstroFinancial Services Docker Images${NC}"
echo -e "${YELLOW}Registry: ${REGISTRY}${NC}"
echo -e "${YELLOW}Tag: ${TAG}${NC}"

# Build base image first
echo -e "\n${GREEN}📦 Building base image...${NC}"
docker build -f docker/Dockerfile.base -t astrofinancial-base:${TAG} .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Base image built successfully${NC}"
else
    echo -e "${RED}❌ Base image build failed${NC}"
    exit 1
fi

# Build service images
services=("backfill" "backtesting" "recommendation")

for service in "${services[@]}"; do
    echo -e "\n${GREEN}📦 Building ${service}-service...${NC}"

    docker build \
        -f docker/Dockerfile.${service} \
        -t ${REGISTRY}/${service}-service:${TAG} \
        .

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ${service}-service built successfully${NC}"
    else
        echo -e "${RED}❌ ${service}-service build failed${NC}"
        exit 1
    fi
done

# Push images if requested
if [ "$PUSH" = "true" ]; then
    echo -e "\n${GREEN}📤 Pushing images to registry...${NC}"

    for service in "${services[@]}"; do
        echo -e "${YELLOW}Pushing ${service}-service...${NC}"
        docker push ${REGISTRY}/${service}-service:${TAG}
    done

    echo -e "${GREEN}✅ All images pushed successfully${NC}"
fi

echo -e "\n${GREEN}🎉 Build completed successfully!${NC}"
echo -e "${YELLOW}Built images:${NC}"
for service in "${services[@]}"; do
    echo -e "  • ${REGISTRY}/${service}-service:${TAG}"
done

echo -e "\n${YELLOW}To run locally with docker-compose:${NC}"
echo -e "  docker-compose up -d"

echo -e "\n${YELLOW}To test a specific service:${NC}"
echo -e "  docker run -p 8001:8001 ${REGISTRY}/backfill-service:${TAG}"