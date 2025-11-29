import logging
from google.adk.agents import LlmAgent
from google.genai import types
from src.Prompts.OrchestratorPrompt import system_prompt
from google.adk.tools import agent_tool
from src.agent.housinggoal import housing_goalagent
from src.agent.BankData import bank_data_agent
from src.agent.RiskProfiler import risk_profiler_agent
from src.agent.PlanGenerator import plan_generator_agent

logger = logging.getLogger(__name__)

logger.info("Initializing housing_goal_agent")

orchestrator_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='orchestrator_agent',
    generate_content_config=types.GenerateContentConfig(
        temperature=0,  # More deterministic output
        max_output_tokens=2500,
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            )
        ]
    ),
    description="""The agent talks to the user to understand thier housing needs and works with a set of 
     agents to help teh user with a plan acheive thier housing needs""",
    instruction= system_prompt, 
    tools=[agent_tool.AgentTool(agent=housing_goalagent),
           agent_tool.AgentTool(agent=bank_data_agent),
           agent_tool.AgentTool(agent=risk_profiler_agent),
           agent_tool.AgentTool(agent=plan_generator_agent)
           ],
)