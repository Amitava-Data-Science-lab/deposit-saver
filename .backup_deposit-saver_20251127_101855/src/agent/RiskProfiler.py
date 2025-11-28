import logging
from google.adk.agents import LlmAgent
from google.genai import types
from src.tools.FinancialTools import risk_classification
from src.tools.utils import retry_config
from src.Prompts.RiskProfilerPrompt import system_prompt
from src.tools.utils import system_safety_settings
from src.agent.schema import RiskProfileInput



logger = logging.getLogger(__name__)


logger.info("Initializing Risk_profiler_agent")

risk_profiler_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="risk_profiler_agent",
    description=(
        "Classifies the user's risk band from 1-4 and sets a max equity share."
    ),
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=1000,
        safety_settings=system_safety_settings
    ),
    instruction=system_prompt,
    input_schema=RiskProfileInput,
    output_key="risk_profile",
    tools=[risk_classification],
   
)
