import logging
from google.adk.tools import ToolContext, FunctionTool

from typing import Any

logger = logging.getLogger(__name__)

def update_state(state_key: str, state_value: Any, tool_context: ToolContext) -> str:
    """Updates a user-specific preference."""
    user_prefs_key = f"user:{state_key}"
    # Get current preferences or initialize if none exist
    user_state = tool_context.state.get(user_prefs_key, {})
    user_state[state_key] = state_value
    # Write the updated dictionary back to the state
    tool_context.state[user_prefs_key] = user_state
    logger.info(f"Tool: Updated user state '{state_key}' to '{state_value}'")
    return {"status": "success", "updated_state": user_state}

state_persister_tool = FunctionTool(func=update_state)
    



