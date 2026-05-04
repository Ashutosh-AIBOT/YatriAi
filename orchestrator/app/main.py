from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
from .agents.base import AgentProtocol
from .agents.transport import search as transport_search
from .agents.cab import compare as cab_compare
from .agents.hotel import search as hotel_search
from .agents.food import find as food_find
from .agents.places import discover as places_discover
from .agents.maps import build_route as map_route

logger = logging.getLogger(__name__)

# ---- Pydantic Request/Response Models ----

class ChatRequest(BaseModel):
    trip_id: str = ""
    user_id: str = "anonymous"
    message: str
    session_id: str = "default"
    user_prefs: Optional[Dict[str, Any]] = None
    action: Optional[str] = None       # "plan_trip" to start planning mode
    target_agent: Optional[str] = None  # Invoke a single agent by name
    wanderlust_enabled: Optional[bool] = None   # Toggle motivator on/off
    wanderlust_intensity: Optional[int] = None   # 0-100 intensity slider
    psychology_enabled: Optional[bool] = None    # Continuous psychology profiling

class ChatResponse(BaseModel):
    trip_id: str
    message: str
    stage: int
    plan: Optional[Dict] = None
    ui_type: str = "text"
    ui_data: Optional[Any] = None
    collected_info: Optional[Dict] = None
    chat_mode: str = "chat"
    agent_statuses: Optional[Dict] = None      # Real-time agent status
    overall_confidence: Optional[float] = None
    ragas_result: Optional[Dict] = None
    wanderlust_message: Optional[str] = None    # Latest motivational message
    user_prefs: Optional[Dict] = None
    plan_status: Optional[str] = None
    finalized_plan: Optional[Dict] = None
    has_finalized_plan: bool = False

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
    version="3.0.0",
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
        "requested_stops": None, "selected_places": None,
        "preferred_place_candidates": None, "transport_modes": None,
        "start_date": None, "end_date": None, "trip_days": None,
        "total_budget": None, "group_size": None,
        "hotel_stars": None, "is_vegetarian": None,
        "cuisine_preferences": None, "interest_tags": None,
        "allow_suggestions": True,
        "transport_results": None, "cab_results": None,
        "hotel_results": None, "food_results": None,
        "places_results": None, "map_results": None,
        "final_plan": None, "plan_status": None, "finalized_plan": None,
        "last_research_snapshot": None, "research_count": 0, "error": None,
        # New orchestration fields
        "agent_statuses": None,
        "overall_confidence": None,
        "ragas_result": None,
        "research_pass": 0,
        "target_agent": None,
        # Wanderlust agent
        "wanderlust_enabled": False,
        "wanderlust_intensity": 50,
        "wanderlust_results": None,
        "psychology_enabled": True,
        "psychology_results": None,
    }

def _get_collected_info(state: dict) -> dict:
    """Return what we know about the trip so far."""
    collected = {}
    for field in ["origin", "destination", "trip_type", "transport_modes",
                   "start_date", "end_date", "trip_days", "total_budget", "group_size",
                   "hotel_stars", "is_vegetarian", "cuisine_preferences",
                   "interest_tags", "requested_stops", "selected_places"]:
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
        "version": "3.0.0",
        "redis": redis_status,
        "llm": "groq-llama-3.1-8b-instant",
        "agents": ["transport", "cabs", "hotels", "food", "places", "maps", "psychology"],
        "features": ["a2a", "confidence_scoring", "ragas_check", "streaming"]
    }

@app.get("/api/v1/history")
async def get_history():
    """Fetch all past chat sessions from Redis."""
    try:
        r = await get_redis()
        if not r:
            return {"history": []}
            
        keys = await r.keys("trip_state:*")
        history = []
        for key in keys:
            raw = await r.get(key)
            if raw:
                try:
                    state = json.loads(raw)
                    # Extract preview data
                    session_id = key.split(":")[1]
                    messages = state.get("messages", [])
                    preview = "No messages yet"
                    if messages:
                        preview = messages[-1].get("content", "")[:50] + "..."
                        
                    history.append({
                        "session_id": session_id,
                        "trip_id": state.get("trip_id"),
                        "origin": state.get("origin"),
                        "destination": state.get("destination"),
                        "plan_status": state.get("plan_status"),
                        "has_finalized_plan": bool(state.get("finalized_plan")),
                        "plan_title": (state.get("finalized_plan") or state.get("final_plan") or {}).get("title"),
                        "preview": preview,
                        "updated_at": state.get("updated_at", "")
                    })
                except Exception:
                    pass
        return {"history": history}
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return {"history": []}

@app.get("/api/v1/history/{session_id}")
async def get_session(session_id: str):
    """Fetch a specific session."""
    try:
        r = await get_redis()
        if not r:
            raise HTTPException(status_code=503, detail="Redis unavailable")
        
        raw = await r.get(f"trip_state:{session_id}")
        if not raw:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return json.loads(raw)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal error")

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

        # 3. Handle single agent invocation
        if req.target_agent:
            state["target_agent"] = req.target_agent

        # 4. Inject user message
        state["messages"].append({"role": "user", "content": req.message})

        # 5. Update user prefs if provided
        if req.user_prefs:
            state["user_prefs"] = req.user_prefs

        # 5b. Update wanderlust settings
        if req.wanderlust_enabled is not None:
            state["wanderlust_enabled"] = req.wanderlust_enabled
        if req.wanderlust_intensity is not None:
            state["wanderlust_intensity"] = req.wanderlust_intensity
        if req.psychology_enabled is not None:
            state["psychology_enabled"] = req.psychology_enabled

        # 6. Run LangGraph state machine
        result = await trip_graph.ainvoke(state)

        # 7. Clear target_agent after use
        result["target_agent"] = None

        # 8. Persist updated state to Redis (if available)
        if r:
            try:
                await r.set(state_key, json.dumps(result, default=str), ex=86400)  # 24h TTL
            except Exception as e:
                logger.warning(f"Could not save state to Redis: {e}")

        # 9. Extract last assistant message
        assistant_msgs = [m for m in result.get("messages", []) if m.get("role") == "assistant"]
        last_msg = assistant_msgs[-1]["content"] if assistant_msgs else "Processing your request..."

        # 10. Determine UI type for rich rendering
        ui_type = "text"
        ui_data = None

        if req.target_agent:
            target_map = {
                "transport": ("transport", "transport_results"),
                "cabs": ("cab", "cab_results"),
                "hotels": ("hotel", "hotel_results"),
                "food": ("food", "food_results"),
                "places": ("places", "places_results"),
                "maps": ("map", "map_results"),
                "psychology": ("psychology", "psychology_results"),
            }
            if req.target_agent in target_map:
                mapped_type, result_key = target_map[req.target_agent]
                if result.get(result_key) and not isinstance(result[result_key], str):
                    ui_type = mapped_type
                    ui_data = result[result_key]
        
        # If no targeted agent override, fall back to checking what got generated
        if ui_type == "text":
            if result.get("final_plan") and result["final_plan"].get("days"):
                ui_type = "plan"
                ui_data = result["final_plan"]
            elif result.get("transport_results") and not isinstance(result["transport_results"], str):
                ui_type = "transport"
                ui_data = result["transport_results"]
            elif result.get("cab_results") and not isinstance(result["cab_results"], str):
                ui_type = "cab"
                ui_data = result["cab_results"]
            elif result.get("hotel_results") and not isinstance(result["hotel_results"], str):
                ui_type = "hotel"
                ui_data = result["hotel_results"]
            elif result.get("food_results") and not isinstance(result["food_results"], str):
                ui_type = "food"
                ui_data = result["food_results"]
            elif result.get("places_results") and not isinstance(result["places_results"], str):
                ui_type = "places"
                ui_data = result["places_results"]
            elif result.get("map_results") and not isinstance(result["map_results"], str):
                ui_type = "map"
                ui_data = result["map_results"]
            elif result.get("psychology_results") and not isinstance(result["psychology_results"], str):
                ui_type = "psychology"
                ui_data = result["psychology_results"]

        return ChatResponse(
            trip_id=result.get("trip_id", req.trip_id),
            message=last_msg,
            stage=result.get("current_stage", 1),
            plan=result.get("final_plan"),
            ui_type=ui_type,
            ui_data=ui_data,
            collected_info=_get_collected_info(result),
            chat_mode=result.get("chat_mode", "chat"),
            agent_statuses=result.get("agent_statuses"),
            overall_confidence=result.get("overall_confidence"),
            ragas_result=result.get("ragas_result"),
            wanderlust_message=(result.get("wanderlust_results") or {}).get("wanderlust_message"),
            user_prefs=result.get("user_prefs"),
            plan_status=result.get("plan_status"),
            finalized_plan=result.get("finalized_plan"),
            has_finalized_plan=bool(result.get("finalized_plan")),
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        # NEVER crash — always return a graceful message
        return ChatResponse(
            trip_id=req.trip_id or "error",
            message=f"I'm sorry, something went wrong on my end. Please try again. (Error: {str(e)[:100]})",
            stage=1,
            ui_type="text",
            chat_mode="chat",
            plan_status=None,
            finalized_plan=None,
            has_finalized_plan=False,
        )


@app.post("/api/v1/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    SSE streaming endpoint — sends real-time agent status updates during plan generation.
    Used by the frontend to show live agent activity.
    """
    async def event_generator():
        try:
            # 1. Load or init state
            state = None
            r = await get_redis()
            state_key = f"trip_state:{req.session_id}"

            if r:
                try:
                    raw = await r.get(state_key)
                    if raw:
                        state = json.loads(raw)
                except Exception:
                    pass

            if state is None:
                state = _init_state(req)

            # Setup
            if req.action == "plan_trip":
                state["chat_mode"] = "planning"
                if not req.message or req.message == "plan_trip":
                    req.message = "I want to plan a trip"

            if req.target_agent:
                state["target_agent"] = req.target_agent
            if req.user_prefs:
                state["user_prefs"] = req.user_prefs

            state["messages"].append({"role": "user", "content": req.message})

            # Phase 1: Smart Chat (LLM processing)
            yield _sse_event("phase", {"phase": "chat", "message": "Processing your message..."})
            await asyncio.sleep(0.1)  # Allow SSE to flush

            # Run the full graph
            result = await trip_graph.ainvoke(state)
            result["target_agent"] = None

            # Stream agent statuses if they exist
            agent_statuses = result.get("agent_statuses")
            if agent_statuses:
                for agent_name, status in agent_statuses.items():
                    yield _sse_event("agent_status", {
                        "agent": agent_name,
                        **status
                    })
                    await asyncio.sleep(0.05)

            # Stream confidence
            if result.get("overall_confidence") is not None:
                yield _sse_event("confidence", {
                    "score": result["overall_confidence"],
                    "agent_statuses": {
                        k: {"status": v.get("status"), "confidence": v.get("confidence")}
                        for k, v in (agent_statuses or {}).items()
                    }
                })

            # Stream RAGAS result
            if result.get("ragas_result"):
                yield _sse_event("ragas", result["ragas_result"])

            # Persist state
            if r:
                try:
                    await r.set(state_key, json.dumps(result, default=str), ex=86400)
                except Exception:
                    pass

            # Final result
            assistant_msgs = [m for m in result.get("messages", []) if m.get("role") == "assistant"]
            last_msg = assistant_msgs[-1]["content"] if assistant_msgs else "Done!"

            ui_type = "text"
            ui_data = None
            if result.get("final_plan") and result["final_plan"].get("days"):
                ui_type = "plan"
                ui_data = result["final_plan"]
            elif result.get("transport_results") and not isinstance(result["transport_results"], str):
                ui_type = "transport"
                ui_data = result["transport_results"]
            elif result.get("cab_results") and not isinstance(result["cab_results"], str):
                ui_type = "cab"
                ui_data = result["cab_results"]
            elif result.get("hotel_results") and not isinstance(result["hotel_results"], str):
                ui_type = "hotel"
                ui_data = result["hotel_results"]
            elif result.get("food_results") and not isinstance(result["food_results"], str):
                ui_type = "food"
                ui_data = result["food_results"]
            elif result.get("places_results") and not isinstance(result["places_results"], str):
                ui_type = "places"
                ui_data = result["places_results"]
            elif result.get("map_results") and not isinstance(result["map_results"], str):
                ui_type = "map"
                ui_data = result["map_results"]
            elif result.get("psychology_results") and not isinstance(result["psychology_results"], str):
                ui_type = "psychology"
                ui_data = result["psychology_results"]

            yield _sse_event("result", {
                "trip_id": result.get("trip_id", ""),
                "message": last_msg,
                "stage": result.get("current_stage", 1),
                "plan": result.get("final_plan"),
                "ui_type": ui_type,
                "ui_data": ui_data,
                "collected_info": _get_collected_info(result),
                "chat_mode": result.get("chat_mode", "chat"),
                "agent_statuses": agent_statuses,
                "overall_confidence": result.get("overall_confidence"),
                "ragas_result": result.get("ragas_result"),
                "wanderlust_message": (result.get("wanderlust_results") or {}).get("wanderlust_message"),
                "user_prefs": result.get("user_prefs"),
                "plan_status": result.get("plan_status"),
                "finalized_plan": result.get("finalized_plan"),
                "has_finalized_plan": bool(result.get("finalized_plan")),
            })

            yield _sse_event("done", {})

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield _sse_event("error", {"message": str(e)[:200]})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


def _sse_event(event_type: str, data: Any) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"
