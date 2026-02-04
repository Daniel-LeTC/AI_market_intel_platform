#!/bin/bash
set -e

# Configuration
VM_IP="34.87.30.120"
VM_USER="${1:-daniel}"  # Default to 'daniel', accept arg1 override
REMOTE_DIR="~/bright-scraper"
SSH_KEY="$HOME/.ssh/google_compute_engine"

# Check if GCloud Key exists, otherwise fallback to default
if [ -f "$SSH_KEY" ]; then
    echo "🔑 Found GCloud Key: $SSH_KEY"
    SSH_OPT="-i $SSH_KEY -o StrictHostKeyChecking=no"
else
    echo "⚠️ GCloud Key not found at $SSH_KEY, using default agent..."
    SSH_OPT=""
fi

echo "🚀 [Deploy] Deploying to $VM_USER@$VM_IP..."

# 1. Upload Configuration
echo "Vk Uploading config files (docker-compose.prod.yml, .env)..."
scp $SSH_OPT docker-compose.prod.yml .env $VM_USER@$VM_IP:$REMOTE_DIR/

# 2. Remote Update
echo "🔄 Triggering Remote Update..."
ssh $SSH_OPT $VM_USER@$VM_IP "cd $REMOTE_DIR && \
    echo '⬇️ Pulling new images...' && \
    docker compose -f docker-compose.prod.yml pull && \
    echo '🔄 Restarting containers...' && \
    docker compose -f docker-compose.prod.yml up -d --remove-orphans && \
    echo '🧹 Cleaning up old images...' && \
    docker image prune -f"

echo "✅ [Deploy] Remote Deployment Complete!"