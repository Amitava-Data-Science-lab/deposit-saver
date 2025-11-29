import logging
from google.adk.agents import LlmAgent
from src.Prompts.OrchestratorPrompt import system_prompt
from google.adk.tools import agent_tool
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types
from src.agent.housinggoal import housing_goalagent
from src.agent.BankData import bank_data_agent
from src.agent.RiskProfiler import risk_profiler_agent
from src.agent.PlanGenerator import plan_generator_agent
from src.tools.StatePersisterTool import after_tool_store_state
from src.agent.WorkflowRouterAgent import workflow_router_agent
from src.tools.utils import system_safety_settings, compact_state_callback, after_tool_store_prefs


logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('housing_goal_agent.log')
    ]
)

logger.info("Initializing housing_goal_agent")
"""
vertexai.init(
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ["GOOGLE_CLOUD_LOCATION"],
    staging_bucket=os.environ["GOOGLE_CLOUD_STAGING_BUCKET"],
)
"""


def session_service_builder():
  logger.info("Building session service")
  service = InMemorySessionService()
  logger.debug(f"Session service created: {type(service).__name__}")
  return service

def memory_service_builder():
  logger.info("Building memory service")
  service = InMemoryMemoryService()
  logger.debug(f"Memory service created: {type(service).__name__}")
  return service

logger.info("Initializing root orchestrator agent")
logger.debug("Configuring agent with model: gemini-2.5-flash, temperature: 0.3, max_output_tokens: 10000")

def debug_state(callback_context, llm_response):
    s = callback_context.state
    if s is None:
        logger.info("NO STATE")
        return
    logger.debug("FULL STATE VIEW: %s", s.to_dict())
    logger.debug("USER PREFS: %s", s.get("user:preferences"))


root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='mortgage_deposit_agent',
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,  # More deterministic output
        max_output_tokens=10000,
        safety_settings=system_safety_settings
    ),
    description="""The agent talks to the user to understand thier housing needs and works with a set of
     agents to help teh user with a plan acheive thier housing needs""",
    instruction= system_prompt,
    tools=[agent_tool.AgentTool(agent=housing_goalagent),
           agent_tool.AgentTool(agent=bank_data_agent),
           agent_tool.AgentTool(agent=risk_profiler_agent),
           agent_tool.AgentTool(agent=plan_generator_agent),
           agent_tool.AgentTool(agent=workflow_router_agent),
           PreloadMemoryTool()],
    after_tool_callback=after_tool_store_state,
    after_model_callback=debug_state
)

logger.info("Root orchestrator agent successfully initialized")
logger.debug(f"Agent tools configured: {len(root_agent.tools)} tools")
