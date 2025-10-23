#!/bin/bash

# Configuration
REGISTRY="your-registry.example.com"  # Change this to your private registry
IMAGE_NAME="telegram-bot"
TAG="${1:-latest}"  # Use argument or default to 'latest'

FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"

echo "Building Docker image..."
echo "Image: ${FULL_IMAGE}"
echo ""

# Build the image
docker build -t "${FULL_IMAGE}" .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "Pushing to registry..."
    docker push "${FULL_IMAGE}"

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Push successful!"
        echo ""
        echo "Image available at: ${FULL_IMAGE}"
        echo ""
        echo "To run locally:"
        echo "  docker run --env-file .env ${FULL_IMAGE}"
    else
        echo ""
        echo "❌ Push failed!"
        echo "Make sure you're logged in to your registry:"
        echo "  docker login ${REGISTRY}"
        exit 1
    fi
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi
