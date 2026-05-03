from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import json
import logging
import uuid

from .config import settings
from .graph.graph import trip_graph
from .graph.state import TripState
from .services.cache import get_redis
from .kafka.consumer import price_monitor_loop

logger = logging.getLogger(__name__)

# ---- Pydantic Request/Response Models ----

class ChatRequest(BaseModel):
    trip_id: str = ""
    user_id: str = "anonymous"
    message: str
    session_id: str = "default"
    user_prefs: Optional[Dict[str, Any]] = None
    action: Optional[str] = None  # "plan_trip" to start planning mode

class ChatResponse(BaseModel):
    trip_id: str
    message: str
    stage: int
    plan: Optional[Dict] = None
    ui_type: str = "text"
    ui_data: Optional[Any] = None
    collected_info: Optional[Dict] = None  # Show what we know so far
    chat_mode: str = "chat"  # "chat" or "planning"

# ---- Lifespan (Startup / Shutdown) ----

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Yatra AI Orchestrator starting up...")
    # Start background price monitor (non-blocking)
    task = asyncio.create_task(price_monitor_loop())
    yield
    # Graceful shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Yatra AI Orchestrator shut down gracefully.")

# ---- App Setup ----

app = FastAPI(
    title="YatraAI Orchestrator",
    version="2.0.0",
    lifespan=lifespan
)

# CORS — allow gateway and frontend origins
allowed_origins = settings.cors_allowed_origins.split(",")
allowed_origins.extend(["http://localhost:3000", "http://localhost:8080", "http://localhost:7860"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set(allowed_origins)),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Helper: Init State ----

def _init_state(req: ChatRequest) -> dict:
    return {
        "trip_id": req.trip_id or str(uuid.uuid4()),
        "user_id": req.user_id,
        "user_prefs": req.user_prefs or {},
        "chat_mode": "chat",
        "current_stage": 1,
        "messages": [],
        "origin": None, "destination": None,
        "trip_type": None, "stop_count": None,
        "requested_stops": None, "transport_modes": None,
        "start_date": None, "end_date": None,
        "total_budget": None, "group_size": 1,
        "hotel_stars": None, "is_vegetarian": None,
        "cuisine_preferences": None, "interest_tags": None,
        "allow_suggestions": True,
        "transport_results": None, "cab_results": None,
        "hotel_results": None, "food_results": None,
        "places_results": None, "map_results": None,
        "final_plan": None, "error": None
    }

def _get_collected_info(state: dict) -> dict:
    """Return what we know about the trip so far."""
    collected = {}
    for field in ["origin", "destination", "trip_type", "transport_modes",
                   "start_date", "end_date", "total_budget", "group_size",
                   "hotel_stars", "is_vegetarian", "cuisine_preferences",
                   "interest_tags"]:
        val = state.get(field)
        if val is not None:
            collected[field] = val
    return collected

# ---- Endpoints ----

@app.get("/health")
async def health():
    """Health check with service status."""
    redis_status = "unknown"
    try:
        r = await get_redis()
        if r:
            await r.ping()
            redis_status = "UP"
        else:
            redis_status = "DOWN (running without cache)"
    except Exception:
        redis_status = "DOWN"

    return {
        "status": "ok",
        "service": "orchestrator",
        "redis": redis_status,
        "llm": "groq-llama-3.1-8b-instant"
    }

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Main chat endpoint — routes user message through smart conversational AI."""
    try:
        # 1. Load or init trip state from Redis (if available)
        state = None
        r = await get_redis()
        state_key = f"trip_state:{req.session_id}"

        if r:
            try:
                raw = await r.get(state_key)
                if raw:
                    state = json.loads(raw)
            except Exception as e:
                logger.warning(f"Could not load state from Redis: {e}")

        if state is None:
            state = _init_state(req)

        # 2. Handle "plan_trip" action — switch to planning mode
        if req.action == "plan_trip":
            state["chat_mode"] = "planning"
            if not req.message or req.message == "plan_trip":
                req.message = "I want to plan a trip"

        # 3. Inject user message
        state["messages"].append({"role": "user", "content": req.message})

        # 4. Run LangGraph state machine
        result = await trip_graph.ainvoke(state)

        # 5. Persist updated state to Redis (if available)
        if r:
            try:
                await r.set(state_key, json.dumps(result, default=str), ex=86400)  # 24h TTL
            except Exception as e:
                logger.warning(f"Could not save state to Redis: {e}")

        # 6. Extract last assistant message
        assistant_msgs = [m for m in result.get("messages", []) if m.get("role") == "assistant"]
        last_msg = assistant_msgs[-1]["content"] if assistant_msgs else "Processing your request..."

        # 7. Determine UI type for rich rendering
        ui_type = "text"
        ui_data = None

        if result.get("final_plan"):
            ui_type = "plan"
            ui_data = result["final_plan"]
        elif result.get("cab_results") and not isinstance(result["cab_results"], str):
            ui_type = "cab"
            ui_data = result["cab_results"]
        elif result.get("hotel_results") and not isinstance(result["hotel_results"], str):
            ui_type = "hotel"
            ui_data = result["hotel_results"]
        elif result.get("map_results") and not isinstance(result["map_results"], str):
            ui_type = "map"
            ui_data = result["map_results"]

        return ChatResponse(
            trip_id=result.get("trip_id", req.trip_id),
            message=last_msg,
            stage=result.get("current_stage", 1),
            plan=result.get("final_plan"),
            ui_type=ui_type,
            ui_data=ui_data,
            collected_info=_get_collected_info(result),
            chat_mode=result.get("chat_mode", "chat")
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        # NEVER crash — always return a graceful message
        return ChatResponse(
            trip_id=req.trip_id or "error",
            message=f"I'm sorry, something went wrong on my end. Please try again. (Error: {str(e)[:100]})",
            stage=1,
            ui_type="text",
            chat_mode="chat"
        )
