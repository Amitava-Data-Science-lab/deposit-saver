import logging
from google.adk.agents import LlmAgent
from google.genai import types
from src.tools.FinancialTools import feasibility_calculator
from src.tools.utils import retry_config
from src.Prompts.HousingGoalPrompt import system_prompt
from src.agent.schema import PlanInput
from src.tools.utils import system_safety_settings

logger = logging.getLogger(__name__)

logger.info("Initializing plan_generator_agent")

plan_generator_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='plan_generator_agent',
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,  # More deterministic output
        max_output_tokens=2000,
        safety_settings=system_safety_settings
    ),
    description="""Plan generator agent generates a financial plan to acheive the deposit amount 
    at the end of user's time horizon. The agent provides the investmant plan and the feasibility
    of acheiving the plan.""",
    instruction= system_prompt,
    input_schema=PlanInput,
    output_key="final_plan",
    tools=[feasibility_calculator],
)