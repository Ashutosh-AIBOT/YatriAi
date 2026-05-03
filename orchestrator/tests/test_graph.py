import pytest
from unittest.mock import AsyncMock
from app.graph.state import TripState
from app.graph.graph import trip_graph
from langchain_core.messages import AIMessage

@pytest.mark.asyncio
async def test_graph_extract_to_route(mocker):
    # Mock the LLM to avoid real API calls and need for API keys
    mock_ainvoke = mocker.patch("langchain_groq.ChatGroq.ainvoke", new_callable=AsyncMock)
    mock_ainvoke.return_value = AIMessage(content='{"origin": "Kanpur", "destination": "Noida"}')

    # Initial state
    state = TripState(
        trip_id="123",
        user_id="user_1",
        user_prefs={},
        current_stage=1,
        messages=[{"role": "user", "content": "I want to go from Kanpur to Noida"}]
    )
    
    # Run the graph
    result = await trip_graph.ainvoke(state)
    
    assert result["current_stage"] == 2
    assert result["origin"] == "Kanpur"
    assert result["destination"] == "Noida"
    assert len(result["messages"]) == 2
    assert result["messages"][-1]["role"] == "assistant"
