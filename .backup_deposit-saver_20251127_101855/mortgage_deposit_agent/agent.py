import logging
from google.adk.agents import LlmAgent
from google.genai import types
from src.Prompts.OrchestratorPrompt import system_prompt
from google.adk.tools import agent_tool
from src.agent.housinggoal import housing_goalagent
from src.agent.BankData import bank_data_agent
from src.agent.RiskProfiler import risk_profiler_agent
from src.agent.PlanGenerator import plan_generator_agent
from src.tools.StatePersisterTool import state_persister_tool
from src.tools.utils import system_safety_settings
import os
import vertexai
from vertexai import agent_engines 
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "capstone-project-479414")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
os.environ.setdefault("GOOGLE_CLOUD_STAGING_BUCKET", "gs://capstone-project-479414-staging")


logger = logging.getLogger(__name__)

logger.info("Initializing housing_goal_agent")

vertexai.init(
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ["GOOGLE_CLOUD_LOCATION"],
    staging_bucket=os.environ["GOOGLE_CLOUD_STAGING_BUCKET"],
)

def session_service_builder():

  return InMemorySessionService()

def memory_service_builder():
  
  return InMemoryMemoryService()

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
           agent_tool.AgentTool(agent=bank_data_agent),
           agent_tool.AgentTool(agent=risk_profiler_agent),
           agent_tool.AgentTool(agent=plan_generator_agent),
           state_persister_tool],
)

agent_app = agent_engines.AdkApp(agent=root_agent
             , session_service_builder=session_service_builder
             , memory_service_builder=memory_service_builder
             , enable_tracing=True
             )

remote_app = agent_engines.create(app=agent_app
                         , project=os.environ["GOOGLE_CLOUD_PROJECT"]
                         , location=os.environ["GOOGLE_CLOUD_LOCATION"],
                         # Define required Python packages for your agent to run
                        requirements=[
                            "google-cloud-aiplatform[adk,agent_engines]",
                            "google-genai"
                        ],
                        # Optional: Configure runtime resource controls
                        config={ 
                            "min_instances": 1, 
                            "max_instances": 10,
                            "resource_limits": {"cpu": "2", "memory": "2Gi"} 
                            }
                        )