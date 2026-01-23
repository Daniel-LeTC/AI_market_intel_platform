#!/bin/bash
set -e

# Configuration
VM_IP="34.87.30.120"
VM_USER="${1:-daniel}"
REMOTE_DIR="~/bright-scraper/hot_patch"
CONTAINER_NAME="scout_ui_prod"
SSH_KEY="$HOME/.ssh/google_compute_engine"

# Files to patch (Local -> Remote Container Path)
declare -A FILES
FILES=(
    ["scout_app/Market_Intelligence.py"]="/app/scout_app/Market_Intelligence.py"
    ["scout_app/ui/common.py"]="/app/scout_app/ui/common.py"
)

if [ -f "$SSH_KEY" ]; then
    SSH_OPT="-i $SSH_KEY -o StrictHostKeyChecking=no"
else
    SSH_OPT=""
fi

echo "🩹 [Hot Patch] Patching UI directly to container..."

# 1. Create temp dir on remote
echo "mkdir -p $REMOTE_DIR"
ssh $SSH_OPT $VM_USER@$VM_IP "mkdir -p $REMOTE_DIR"

# 2. Loop through files
for LOCAL in "${!FILES[@]}"; do
    REMOTE_DEST="${FILES[$LOCAL]}"
    FILENAME=$(basename "$LOCAL")
    
    echo "---------------------------------------------------"
    echo "📤 Uploading $LOCAL..."
    scp $SSH_OPT "$LOCAL" $VM_USER@$VM_IP:$REMOTE_DIR/$FILENAME
    
    echo "💉 Injecting into $CONTAINER_NAME ($REMOTE_DEST)..."
    ssh $SSH_OPT $VM_USER@$VM_IP "docker cp $REMOTE_DIR/$FILENAME $CONTAINER_NAME:$REMOTE_DEST"
done

# 3. Touch main file to force reload
echo "🔄 Touching main file to force Streamlit reload..."
ssh $SSH_OPT $VM_USER@$VM_IP "docker exec $CONTAINER_NAME touch /app/scout_app/Market_Intelligence.py"

echo "---------------------------------------------------"
echo "✅ [Hot Patch] Done! Streamlit should auto-reload."