#!/bin/bash
set -e

# Configuration
VM_IP="34.87.30.120"
VM_USER="${1:-daniel}"
REMOTE_DIR="~/bright-scraper/hot_patch"
SSH_KEY="$HOME/.ssh/google_compute_engine"

# Files Map: "Local Path" -> "Container Name : Container Path"
declare -A FILES
FILES=(
    ["scout_app/Market_Intelligence.py"]="scout_ui_prod:/app/scout_app/Market_Intelligence.py"
    ["scout_app/ui/common.py"]="scout_ui_prod:/app/scout_app/ui/common.py"
    ["scout_app/ui/tabs/xray.py"]="scout_ui_prod:/app/scout_app/ui/tabs/xray.py"
    ["worker_api.py"]="scout_worker_prod:/app/worker_api.py"
)

if [ -f "$SSH_KEY" ]; then
    SSH_OPT="-i $SSH_KEY -o StrictHostKeyChecking=no"
else
    SSH_OPT=""
fi

echo "🩹 [Hot Patch] Patching System Components..."

# 1. Create temp dir on remote
echo "mkdir -p $REMOTE_DIR"
ssh $SSH_OPT $VM_USER@$VM_IP "mkdir -p $REMOTE_DIR"

# 2. Loop through files
for LOCAL in "${!FILES[@]}"; do
    TARGET_INFO="${FILES[$LOCAL]}"
    CONTAINER_NAME="${TARGET_INFO%%:*}"
    REMOTE_DEST="${TARGET_INFO#*:}"
    FILENAME=$(basename "$LOCAL")
    
    echo "---------------------------------------------------"
    echo "📤 Uploading $LOCAL..."
    scp $SSH_OPT "$LOCAL" $VM_USER@$VM_IP:$REMOTE_DIR/$FILENAME
    
    echo "💉 Injecting into $CONTAINER_NAME ($REMOTE_DEST)..."
    ssh $SSH_OPT $VM_USER@$VM_IP "docker cp $REMOTE_DIR/$FILENAME $CONTAINER_NAME:$REMOTE_DEST"
done

# 3. Reload Strategy
echo "---------------------------------------------------"
echo "🔄 Reloading Components..."

# UI: Touch main file to auto-reload
ssh $SSH_OPT $VM_USER@$VM_IP "docker exec scout_ui_prod touch /app/scout_app/Market_Intelligence.py"
echo "✅ UI Reloaded (Hot)"

# Worker: Restart needed for code changes
ssh $SSH_OPT $VM_USER@$VM_IP "docker restart scout_worker_prod"
echo "✅ Worker Restarted"

echo "---------------------------------------------------"
echo "🎉 System Patched & Ready!"