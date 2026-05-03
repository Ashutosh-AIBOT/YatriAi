from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from .graph.graph import trip_graph
from .graph.state import TripState

app = FastAPI(title="Yatra AI Orchestrator")

class ChatRequest(BaseModel):
    trip_id: str
    user_id: str
    message: str

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    # Retrieve current state from DB (dummy implementation here)
    # Ideally, we would fetch the state from the database
    state = TripState(
        trip_id=request.trip_id,
        user_id=request.user_id,
        user_prefs={},
        current_stage=1,
        messages=[{"role": "user", "content": request.message}]
    )
    
    # Run the state machine
    try:
        new_state = await trip_graph.ainvoke(state)
        return {"status": "success", "state": new_state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
