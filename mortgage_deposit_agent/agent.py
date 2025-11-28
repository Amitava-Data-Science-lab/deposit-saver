import logging
from google.adk.agents import LlmAgent
from google.genai import types, Client
from src.Prompts.OrchestratorPrompt import system_prompt
from google.adk.tools import agent_tool
from src.agent.housinggoal import housing_goalagent
from src.agent.FinancialInstrument import financial_instrument_agent
from src.agent.RiskProfiler import risk_profiler_agent
from src.agent.PlanGenerator import plan_generator_agent
from src.tools.StatePersisterTool import state_persister_tool
from src.tools.utils import system_safety_settings
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools.preload_memory_tool import PreloadMemoryTool


logger = logging.getLogger(__name__)

logger.info("Initializing housing_goal_agent")
"""
vertexai.init(
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ["GOOGLE_CLOUD_LOCATION"],
    staging_bucket=os.environ["GOOGLE_CLOUD_STAGING_BUCKET"],
)
"""
MAX_HISTORY_MESSAGES = 20

def session_service_builder():

  return InMemorySessionService()

def memory_service_builder():
  
  return InMemoryMemoryService()

async def _summarise_history(messages: list[str]) -> str:
    if not messages:
        return ""

    # Build a simple plain-text block
    text_block = "\n".join(messages)

    # Use the same model as your agent via the ADK client in the context
    client = Client()  # ADK wires this up

    resp = await client.models.generate_content_async(
        model="gemini-2.5-flash",  # you can also use callback_context.model_name if you prefer
        contents=f"""Summarise the following conversation so far in a concise way,
focusing on the user's housing goals, constraints, preferences, and key facts:

{text_block}
""",
    )
    return resp.text.strip()

async def compact_state_callback(callback_context):
    state = callback_context.state

    # 1) Get conversation history – assume it’s a list of strings or dicts
    history = state.get("conversation:history", [])
    if not history or len(history) <= MAX_HISTORY_MESSAGES:
        # Nothing to compact – still also call your memory save
        await auto_save_session_to_memory_callback(callback_context)
        return

    # 2) Split into old vs new
    old_messages = history[:-MAX_HISTORY_MESSAGES]
    recent_messages = history[-MAX_HISTORY_MESSAGES:]

    # Convert old messages to strings if they are dicts
    def msg_to_text(m):
        if isinstance(m, dict):
            return f'{m.get("role", "")}: {m.get("text", "")}'
        return str(m)

    old_texts = [msg_to_text(m) for m in old_messages]

    # 3) Summarise the old part
    summary_text = await _summarise_history(old_texts)

    # 4) Replace history in state with summary + recent messages
    new_history = []
    if summary_text:
        new_history.append({"role": "system", "text": f"[Summary so far] {summary_text}"})
    new_history.extend(recent_messages)
    state["conversation:history"] = new_history

    # 5) Optional: clean up stale temporary keys
    for key in list(state.keys()):
        if key.startswith("temp:"):
            del state[key]

    # 6) Also keep your existing memory save behavior
    await auto_save_session_to_memory_callback(callback_context)


async def auto_save_session_to_memory_callback(callback_context):
    session = getattr(callback_context, "session", None)
    memory_service = getattr(callback_context, "memory_service", None)

    # Fallback to invocation context for older ADK versions
    if session is None and hasattr(callback_context, "_invocation_context"):
        session = callback_context._invocation_context.session
    if memory_service is None and hasattr(callback_context, "_invocation_context"):
        memory_service = callback_context._invocation_context.memory_service

    if not session or not memory_service:
        return  # nothing to do

    await memory_service.add_session_to_memory(session)

async def after_tool_store_prefs(tool, args, tool_context, tool_response):
    state = tool_context.state

    # Detect if this tool is an AgentTool and has an output_key
    output_key = None
    if hasattr(tool, "agent") and getattr(tool.agent, "output_key", None):
        output_key = tool.agent.output_key

    if not output_key:
        # Tool doesn't have an output key → nothing to persist
        return None

    # Read the agent-as-tool output
    agent_output = state.get(output_key)
    if agent_output is None:
        return None

    # Update user preferences
    user_prefs = state.get("user:preferences", {})
    agent_prefs = user_prefs.get("agent_outputs", {})
    agent_prefs[tool.agent.name] = agent_output
    user_prefs["agent_outputs"] = agent_prefs
    state["user:preferences"] = user_prefs

    return None
    
root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='orchestrator_agent',
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,  # More deterministic output
        max_output_tokens=10000,
        safety_settings=system_safety_settings
    ),
    description="""The agent talks to the user to understand thier housing needs and works with a set of 
     agents to help teh user with a plan acheive thier housing needs""",
    instruction= system_prompt, 
    tools=[agent_tool.AgentTool(agent=housing_goalagent),
           agent_tool.AgentTool(agent=financial_instrument_agent),
           agent_tool.AgentTool(agent=risk_profiler_agent),
           agent_tool.AgentTool(agent=plan_generator_agent),
           PreloadMemoryTool(),
           state_persister_tool],
    after_agent_callback=compact_state_callback,
    after_tool_callback=after_tool_store_prefs,
)
