import logging
from google.adk.agents import LlmAgent
from google.genai import types
from src.tools.utils import retry_config
from google.adk.tools import google_search
from src.Prompts.PropertyPricePrompt import system_prompt
from src.agent.schema import HousingGoalInput


logger = logging.getLogger(__name__)

logger.info("Initializing Property_Price_Agent")

property_price_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='property_price_agent',
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
    description="""Determines the price range of a given property type in a given postcode using online web search""",
    instruction= system_prompt, 
    input_schema=HousingGoalInput,
    output_key="house_prices",
    tools=[google_search],
)