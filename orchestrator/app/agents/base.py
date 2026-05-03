"""
Base Agent Protocol — Agent-to-Agent (A2A) Communication

Each sub-agent can:
1. Read results from other agents via shared state
2. Request another agent to run if its data is needed
3. Report its own status/confidence back to the orchestrator
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AgentProtocol:
    """Mixin that provides A2A communication capabilities to any agent."""

    AGENT_NAMES = ["transport", "cabs", "hotels", "food", "places", "maps"]
    RESULT_KEYS = {
        "transport": "transport_results",
        "cabs": "cab_results",
        "hotels": "hotel_results",
        "food": "food_results",
        "places": "places_results",
        "maps": "map_results",
    }

    @staticmethod
    def get_sibling_data(state: dict, agent_name: str) -> Optional[Dict]:
        """A2A: Read another agent's results from shared state."""
        key = AgentProtocol.RESULT_KEYS.get(agent_name)
        if key:
            return state.get(key)
        return None

    @staticmethod
    def has_sibling_data(state: dict, agent_name: str) -> bool:
        """Check if a sibling agent has already produced results."""
        data = AgentProtocol.get_sibling_data(state, agent_name)
        if data is None:
            return False
        if isinstance(data, dict) and data.get("status") == "error":
            return False
        return True

    @staticmethod
    def set_status(state: dict, agent_name: str, status: str,
                   message: str = "", confidence: float = 0,
                   called_agents: Optional[List[str]] = None):
        """Update this agent's status in shared state."""
        if "agent_statuses" not in state or state["agent_statuses"] is None:
            state["agent_statuses"] = {}

        now = datetime.now(timezone.utc).isoformat()
        existing = state["agent_statuses"].get(agent_name, {})

        state["agent_statuses"][agent_name] = {
            "status": status,
            "message": message,
            "confidence": confidence,
            "started_at": existing.get("started_at", now) if status != "researching" else now,
            "finished_at": now if status in ("done", "error") else None,
            "called_agents": called_agents or existing.get("called_agents", []),
            "error": None,
        }

    @staticmethod
    def set_error(state: dict, agent_name: str, error: str):
        """Mark this agent as errored."""
        AgentProtocol.set_status(state, agent_name, "error", f"Failed: {error}", 0)
        state["agent_statuses"][agent_name]["error"] = error

    @staticmethod
    def calculate_agent_confidence(result: Any, agent_name: str) -> float:
        """
        Calculate confidence score for a single agent's results.
        Higher confidence = more/better data returned.
        """
        if result is None or (isinstance(result, dict) and result.get("status") == "error"):
            return 0.0

        if isinstance(result, dict):
            # Check if there's actual data beyond just error fields
            error = result.get("error")
            has_error = error and "not configured" not in str(error).lower()

            # Count data items
            data_count = 0
            for key, val in result.items():
                if key in ("error", "status", "note"):
                    continue
                if isinstance(val, list):
                    data_count += len(val)
                elif isinstance(val, dict) and val:
                    data_count += 1
                elif val and val not in (None, "", 0):
                    data_count += 1

            if data_count == 0:
                return 10.0  # Ran but found nothing
            elif data_count <= 2:
                return 50.0
            elif data_count <= 5:
                return 75.0
            else:
                return 90.0

        return 50.0  # Unknown structure

    @staticmethod
    def calculate_overall_confidence(agent_statuses: Dict[str, Dict]) -> float:
        """
        Aggregate confidence across all agents.
        Rule: If 3+ of 6 agents have confidence >= 50, overall is HIGH.
        """
        if not agent_statuses:
            return 0.0

        scores = []
        for name, status in agent_statuses.items():
            if name in AgentProtocol.AGENT_NAMES:
                scores.append(status.get("confidence", 0))

        if not scores:
            return 0.0

        high_confidence_count = sum(1 for s in scores if s >= 50)
        avg_score = sum(scores) / len(scores)

        # If 3+ agents are confident, boost overall
        if high_confidence_count >= 3:
            return min(95, avg_score * 1.2)
        elif high_confidence_count >= 2:
            return min(80, avg_score * 1.0)
        else:
            return min(60, avg_score * 0.8)

    @staticmethod
    def needs_reresearch(agent_statuses: Dict[str, Dict]) -> List[str]:
        """Determine which agents should re-research for better results."""
        weak_agents = []
        for name, status in agent_statuses.items():
            if name in AgentProtocol.AGENT_NAMES:
                conf = status.get("confidence", 0)
                if conf < 40 and status.get("status") != "error":
                    weak_agents.append(name)
        return weak_agents
