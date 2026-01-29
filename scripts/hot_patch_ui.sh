#!/bin/bash
set -e

# Configuration
VM_IP="34.87.30.120"
VM_USER="${1:-daniel}"
REMOTE_DIR="~/bright-scraper/hot_patch"
UI_CONTAINER="scout_ui_prod"
WORKER_CONTAINER="scout_worker_prod"
SSH_KEY="$HOME/.ssh/google_compute_engine"

# Files to patch (Local -> Remote Container Path)
declare -A FILES
FILES=(
    ["scout_app/Market_Intelligence.py"]="/app/scout_app/Market_Intelligence.py"
    ["scout_app/ui/common.py"]="/app/scout_app/ui/common.py"
    ["scout_app/core/ingest.py"]="/app/scout_app/core/ingest.py"
    ["scout_app/core/stats_engine.py"]="/app/scout_app/core/stats_engine.py"
    ["worker_api.py"]="/app/worker_api.py"
)

if [ -f "$SSH_KEY" ]; then
    SSH_OPT="-i $SSH_KEY -o StrictHostKeyChecking=no"
else
    SSH_OPT=""
fi

echo "🩹 [Hot Patch] Patching UI & Worker directly to containers..."

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
    
    echo "💉 Injecting into $UI_CONTAINER..."
    ssh $SSH_OPT $VM_USER@$VM_IP "docker cp $REMOTE_DIR/$FILENAME $UI_CONTAINER:$REMOTE_DEST"
    
    echo "💉 Injecting into $WORKER_CONTAINER..."
    ssh $SSH_OPT $VM_USER@$VM_IP "docker cp $REMOTE_DIR/$FILENAME $WORKER_CONTAINER:$REMOTE_DEST"
done

# 3. Force reload
echo "🔄 Reloading Streamlit..."
ssh $SSH_OPT $VM_USER@$VM_IP "docker exec $UI_CONTAINER touch /app/scout_app/Market_Intelligence.py"

echo "🔄 Restarting Worker container to apply Core changes..."
ssh $SSH_OPT $VM_USER@$VM_IP "docker restart $WORKER_CONTAINER"

# 4. Upload Staging Data (RnD File)
STAGING_FILE="staging_data/RnD_Test_Ingest_Fixed.xlsx"
if [ -f "$STAGING_FILE" ]; then
    echo "---------------------------------------------------"
    echo "📤 Uploading Staging Data: $STAGING_FILE..."
    scp $SSH_OPT "$STAGING_FILE" $VM_USER@$VM_IP:~/bright-scraper/staging_data/
    ssh $SSH_OPT $VM_USER@$VM_IP "docker cp ~/bright-scraper/staging_data/RnD_Test_Ingest_Fixed.xlsx $UI_CONTAINER:/app/staging_data/"
fi

echo "---------------------------------------------------"
echo "✅ [Hot Patch] Done! Streamlit should auto-reload."