#!/bin/bash
set -e

# Configuration
REGION="asia-southeast1"
PROJECT="br-data-rv"
REPO="bright-repo"
REGISTRY="$REGION-docker.pkg.dev/$PROJECT/$REPO"

echo "🚀 [Build] Starting Build & Push Process..."

# 1. Build Single Image (Base)
echo "🔨 Building Scout Core Image..."
docker build -t scout-core:latest .

# 2. Tag for Registry
echo "🏷️ Tagging for Artifact Registry..."
docker tag scout-core:latest $REGISTRY/scout-ui:latest
docker tag scout-core:latest $REGISTRY/scout-worker:latest

# 3. Push to Registry
echo "⬆️ Pushing Images to GCP..."
docker push $REGISTRY/scout-ui:latest
docker push $REGISTRY/scout-worker:latest

echo "✅ [Build] Build & Push Complete!"
