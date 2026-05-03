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

# 1. Start Postgres & Redis
echo "Booting Databases..."
service postgresql start || echo "Warning: Postgres failed to start"
service redis-server start || echo "Warning: Redis failed to start"

# 2. Start Kafka in KRaft mode
start_service "Kafka" "/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/kraft/server.properties" "logs_kafka.log"
sleep 5 # Give Kafka time to initialize

# 3. Start Gateway (Java Spring Boot)
start_service "Gateway API" "cd /app/gateway && java -jar target/gateway-0.0.1-SNAPSHOT.jar" "logs_gateway.log"

# 4. Start Orchestrator (FastAPI)
start_service "Orchestrator" "cd /app/orchestrator && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8001" "logs_orchestrator.log"

# 5. Start Notification Service (Node.js)
start_service "Notification Websockets" "cd /app/notification && node src/server.js" "logs_notification.log"

# 6. Start Frontend (Next.js) on the exposed port
echo "Booting Next.js Frontend on port 7860..."
cd /app/frontend
export PORT=7860
export NEXT_PUBLIC_GATEWAY_URL="/api/v1"
export NEXT_PUBLIC_NOTIFICATION_URL=""

# Robust frontend start that will catch crashes
npm start || echo "CRITICAL: Frontend crashed. Check logs."
