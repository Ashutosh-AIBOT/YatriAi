#!/bin/bash
echo "========================================="
echo "   Starting Yatra.AI Local Ecosystem"
echo "========================================="

BASE_DIR="$(pwd)"
mkdir -p "$BASE_DIR/logs"

echo "[1/5] Starting Infrastructure (Docker)..."
cd "$BASE_DIR/infra" && docker-compose up -d > "$BASE_DIR/logs/infra.log" 2>&1

echo "[2/5] Starting Gateway (Spring Boot)..."
cd "$BASE_DIR/gateway" && nohup mvn spring-boot:run > "$BASE_DIR/logs/gateway.log" 2>&1 &

echo "[3/5] Starting Orchestrator (FastAPI)..."
cd "$BASE_DIR/orchestrator" && source .venv/bin/activate && nohup uvicorn app.main:app --port 8001 > "$BASE_DIR/logs/orchestrator.log" 2>&1 &

echo "[4/5] Starting Notification Service (Node.js)..."
cd "$BASE_DIR/notification" && nohup node src/server.js > "$BASE_DIR/logs/notification.log" 2>&1 &

echo "[5/5] Starting Frontend (Next.js)..."
cd "$BASE_DIR/frontend" && nohup npm run dev > "$BASE_DIR/logs/frontend.log" 2>&1 &

echo ""
echo "✅ All microservices have been successfully started in the background!"
echo "📡 Frontend is running at: http://localhost:3000"
echo "📊 Gateway is running at: http://localhost:8080"
echo "🧠 Orchestrator is running at: http://localhost:8001"
echo "🔔 Notifications is running at: http://localhost:3001"
echo ""
echo "To view live logs, run: tail -f logs/frontend.log (or any other service log)"
echo "To stop everything, use: pkill -f 'mvn|uvicorn|node|next' && cd infra && docker-compose down"
