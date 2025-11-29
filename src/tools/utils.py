import logging
from google.adk.apps.app import EventsCompactionConfig
from google.genai import types, Client
from src.agent.schema import SessionState

retry_config=types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504], # Retry on these HTTP errors
)

system_safety_settings = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            )
        ]

events_compaction_config=EventsCompactionConfig(
        compaction_interval=10,  # Trigger compaction every 10 new invocations.
        overlap_size=2          # Include last 2 invocation from the previous window.
    )

MAX_HISTORY_MESSAGES = 20

logger = logging.getLogger(__name__)

async def _summarise_history(messages: list[str]) -> str:
    logger.info(f"Summarising history with {len(messages)} messages")
    if not messages:
        logger.debug("No messages to summarise, returning empty string")
        return ""

    # Build a simple plain-text block
    text_block = "\n".join(messages)
    logger.debug(f"Text block length: {len(text_block)} characters")

    # Use the same model as your agent via the ADK client in the context
    client = Client()  # ADK wires this up
    logger.debug("Client initialized for summarisation")

    try:
        resp = await client.models.generate_content_async(
            model="gemini-2.5-flash",  # you can also use callback_context.model_name if you prefer
            contents=f"""Summarise the following conversation so far in a concise way,
focusing on the user's housing goals, constraints, preferences, and key facts:

{text_block}
""",
        )
        summary = resp.text.strip()
        logger.info(f"Successfully generated summary of length: {len(summary)} characters")
        return summary
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}", exc_info=True)
        raise

async def compact_state_callback(callback_context):
    logger.info("Compact state callback initiated")
    state = callback_context.state
    logger.debug(f"State keys: {list(state.keys())}")

    # 1) Get conversation history – assume it's a list of strings or dicts
    history = state.get("conversation:history", [])
    logger.info(f"Current history length: {len(history)} messages")

    if not history or len(history) <= MAX_HISTORY_MESSAGES:
        # Nothing to compact – still also call your memory save
        logger.info(f"History length ({len(history)}) <= MAX_HISTORY_MESSAGES ({MAX_HISTORY_MESSAGES}), skipping compaction")
        await auto_save_session_to_memory_callback(callback_context)
        return

    # 2) Split into old vs new
    old_messages = history[:-MAX_HISTORY_MESSAGES]
    recent_messages = history[-MAX_HISTORY_MESSAGES:]
    logger.info(f"Splitting history: {len(old_messages)} old messages, {len(recent_messages)} recent messages")

    # Convert old messages to strings if they are dicts
    def msg_to_text(m):
        if isinstance(m, dict):
            return f'{m.get("role", "")}: {m.get("text", "")}'
        return str(m)

    old_texts = [msg_to_text(m) for m in old_messages]
    logger.debug(f"Converted {len(old_texts)} old messages to text")

    # 3) Summarise the old part
    try:
        summary_text = await _summarise_history(old_texts)
        logger.info("Successfully summarised old messages")
    except Exception as e:
        logger.error(f"Failed to summarise history: {str(e)}", exc_info=True)
        raise

    # 4) Replace history in state with summary + recent messages
    new_history = []
    if summary_text:
        new_history.append({"role": "system", "text": f"[Summary so far] {summary_text}"})
        logger.debug("Added summary to new history")
    new_history.extend(recent_messages)
    state["conversation:history"] = new_history
    logger.info(f"Compacted history from {len(history)} to {len(new_history)} messages")

    # 5) Optional: clean up stale temporary keys
    temp_keys = [key for key in state.keys() if key.startswith("temp:")]
    if temp_keys:
        logger.debug(f"Cleaning up {len(temp_keys)} temporary keys: {temp_keys}")
        for key in temp_keys:
            del state[key]
    else:
        logger.debug("No temporary keys to clean up")

    # 6) Also keep your existing memory save behavior
    await auto_save_session_to_memory_callback(callback_context)
    logger.info("Compact state callback completed")


async def auto_save_session_to_memory_callback(callback_context):
    logger.info("Auto-save session to memory callback initiated")
    session = getattr(callback_context, "session", None)
    memory_service = getattr(callback_context, "memory_service", None)
    logger.debug(f"Session: {session is not None}, Memory service: {memory_service is not None}")

    # Fallback to invocation context for older ADK versions
    if session is None and hasattr(callback_context, "_invocation_context"):
        session = callback_context._invocation_context.session
        logger.debug("Session retrieved from invocation context")
    if memory_service is None and hasattr(callback_context, "_invocation_context"):
        memory_service = callback_context._invocation_context.memory_service
        logger.debug("Memory service retrieved from invocation context")

    if not session or not memory_service:
        logger.warning("Session or memory service not available, skipping auto-save")
        return  # nothing to do

    try:
        await memory_service.add_session_to_memory(session)
        logger.info("Successfully saved session to memory")
    except Exception as e:
        logger.error(f"Failed to save session to memory: {str(e)}", exc_info=True)
        raise

async def after_tool_store_prefs(tool, args, tool_context, tool_response):
    logger.info(f"After tool callback initiated for tool: {getattr(tool, 'name', 'unknown')}")
    state = tool_context.state
    logger.debug(f"Tool args: {args}")

    session_state: SessionState = None

    # Detect if this tool is an AgentTool and has an output_key
    output_key = None
    if hasattr(tool, "agent") and getattr(tool.agent, "output_key", None):
        output_key = tool.agent.output_key
        logger.info(f"Agent tool detected with output_key: {output_key}")

    if not output_key:
        # Tool doesn't have an output key → nothing to persist
        logger.info("No output key found, skipping preference storage")
        return None

    # Read the agent-as-tool output
    agent_output = state.get(output_key)
    if agent_output is None:
        logger.info(f"No output found for key '{output_key}', skipping preference storage")
        return None

    
    logger.info(f"Storing agent output for: {tool.agent.name}")

    # Update user preferences
    user_prefs = state.get("user:preferences", {})
    agent_prefs = user_prefs.get("agent_outputs", {})
    agent_prefs[tool.agent.name] = agent_output
    user_prefs["agent_outputs"] = agent_prefs
    state["user:preferences"] = user_prefs
    logger.info(f"Successfully stored preferences {user_prefs} for agent: {tool.agent.name}")
    logger.debug(f"Current agent outputs count: {len(agent_prefs)}")

    return None