import logging
from google.adk.agents import LlmAgent
from google.genai import types
from src.tools.FinancialTools import deposit_calculator
from src.tools.utils import retry_config
from src.tools.WebSearch import property_price_search, outcode_checker, nearby_outcodes
from src.Prompts.HousingGoalPrompt import system_prompt
from src.agent.schema import HousingGoalInput


logger = logging.getLogger(__name__)

logger.info("Initializing housing_goal_agent")

housing_goalagent = LlmAgent(
    model='gemini-2.5-flash',
    name='housing_goal_agent',
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,  # More deterministic output
        max_output_tokens=5000,
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            )
        ]
    ),
    description="""Determines a realistic house price and deposit target for a user based on their UK postcode
                and desired property type, using price search and  deposit calculation tools.""",
    instruction= system_prompt, 
    input_schema=HousingGoalInput,
    output_key="housing_goal",
    tools=[deposit_calculator, property_price_search, outcode_checker, nearby_outcodes],
)

