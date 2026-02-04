#!/bin/bash

# Configuration
PROJECT="br-data-rv"
ZONE="asia-southeast1-a"
VM_NAME="bright-scout-vm"

# Usage check
if [ -z "$1" ]; then
    echo "❌ Usage: $0 [start|stop|status]"
    exit 1
fi

ACTION=$1

if [ "$ACTION" == "start" ]; then
    echo "🚀 Starting VM: $VM_NAME..."
    gcloud compute instances start $VM_NAME --project=$PROJECT --zone=$ZONE
    echo "✅ VM Started! Getting new IP..."
    gcloud compute instances describe $VM_NAME --project=$PROJECT --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

elif [ "$ACTION" == "stop" ]; then
    echo "🛑 Stopping VM: $VM_NAME..."
    gcloud compute instances stop $VM_NAME --project=$PROJECT --zone=$ZONE
    echo "💤 VM Stopped. Sleep well!"

elif [ "$ACTION" == "status" ]; then
    gcloud compute instances describe $VM_NAME --project=$PROJECT --zone=$ZONE --format='value(status)'

else
    echo "❌ Unknown command. Use: start, stop, or status"
    exit 1
fi
