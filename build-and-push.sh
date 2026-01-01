#!/bin/bash

# Local build script for development
# For CI/CD, GitHub Actions will handle the build and push

set -e # Exit on error

# Configuration
REGISTRY="ghcr.io"
USERNAME="${GITHUB_ACTOR:-$(git config user.name)}"
IMAGE_NAME="telegram-bot"
TAG="${1:-latest}"

FULL_IMAGE="${REGISTRY}/${USERNAME}/${IMAGE_NAME}:${TAG}"

echo "🔨 Building Docker image locally..."
echo "📦 Image: ${FULL_IMAGE}"
echo ""

# Build the image
docker build -t "${FULL_IMAGE}" .

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Build successful!"
  echo ""
  echo "To push to GHCR:"
  echo "  docker login ghcr.io -u ${USERNAME}"
  echo "  docker push ${FULL_IMAGE}"
  echo ""
  echo "To run locally:"
  echo "  docker run --env-file .env ${FULL_IMAGE}"
  echo ""
  echo "Note: Push will happen automatically via GitHub Actions when you:"
  echo "  git push"
else
  echo ""
  echo "❌ Build failed!"
  exit 1
fi

