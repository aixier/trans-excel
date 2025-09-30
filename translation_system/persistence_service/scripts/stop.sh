#!/bin/bash
# ============================================================================
# Persistence Service - Stop Script
# ============================================================================

echo "Stopping Persistence Service..."

# Find and kill the process
PID=$(ps aux | grep "python main.py" | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
    echo "Persistence Service is not running"
else
    echo "Killing process $PID..."
    kill $PID
    echo "Persistence Service stopped"
fi