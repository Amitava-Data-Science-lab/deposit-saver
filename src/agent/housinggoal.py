import logging
from google.adk.agents import LlmAgent
from google.genai import types
from src.tools.FinancialTools import deposit_calculator
from src.tools.WebSearch import outcode_checker, nearby_outcodes
from src.Prompts.HousingGoalPrompt import system_prompt
from src.agent.schema import HousingGoalInput
from src.agent.PropertyPriceAgent import property_price_agent
from src.tools.utils import system_safety_settings
from google.adk.tools import agent_tool



logger = logging.getLogger(__name__)

logger.info("Initializing housing_goal_agent")

housing_goalagent = LlmAgent(
    model='gemini-2.5-flash',
    name='housing_goal_agent',
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,  # More deterministic output
        max_output_tokens=5000,
        safety_settings=system_safety_settings,
    ),
    description="""Determines a realistic house price and deposit target for a user based on their UK postcode
                and desired property type, using price search and  deposit calculation tools. This agent must be
                used to handle all House and property price related queries.                
                """,
    instruction= system_prompt, 
    input_schema=HousingGoalInput,
    output_key="housing_goal",
    tools=[outcode_checker, 
           agent_tool.AgentTool(agent=property_price_agent), 
           deposit_calculator,
           nearby_outcodes],
)


