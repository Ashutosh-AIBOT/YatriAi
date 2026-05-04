#!/bin/bash
echo "Starting Hugging Face Space Monolith Ecosystem..."

# Helper function for robust background execution
start_service() {
    local name=$1
    local cmd=$2
    local log=$3
    echo "Booting $name..."
    eval "$cmd > /app/$log 2>&1 &"
    # Don't let individual service failures kill the script
}

# 1. Start Redis (Postgres/Kafka optional)
echo "Booting Redis..."
service redis-server start || echo "Warning: Redis failed to start"

# 2. Start Orchestrator (FastAPI) — the critical service
echo "Booting Orchestrator on port 8001..."
cd /app/orchestrator
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 > /app/logs_orchestrator.log 2>&1 &
cd /app

# 3. Wait for orchestrator to be ready
echo "Waiting for Orchestrator to start..."
for i in {1..15}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ Orchestrator is UP!"
        break
    fi
    echo "  Waiting... ($i/15)"
    sleep 2
done

# 4. Start Frontend (Next.js) on the exposed port 7860
echo "Booting Next.js Frontend on port 7860..."
cd /app/frontend
export PORT=7860
export ORCHESTRATOR_URL="http://localhost:8001"
export NEXT_PUBLIC_GATEWAY_URL="/api/v1"
export NEXT_PUBLIC_NOTIFICATION_URL=""

# Robust frontend start that will catch crashes
npm start || echo "CRITICAL: Frontend crashed. Check logs."
