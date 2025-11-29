import logging
from google.adk.agents import LlmAgent
from google.genai import types
from src.tools.FinancialTools import estimate_affordability
from src.tools.FileLoadTool import load_bank_statement
from src.Prompts.BankDataPrompt import system_prompt
from src.tools.utils import system_safety_settings
from src.agent.schema import BankDataInput



logger = logging.getLogger(__name__)


logger.info("Initializing bank_data_agent")

bank_data_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='bank_data_agent',
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,  # More deterministic output
        max_output_tokens=8000,
        safety_settings=system_safety_settings
    ),
    description="""Determines a realistic disposable investmant amount for the user based on the bank statements""",
    instruction= system_prompt,
    input_schema=BankDataInput,
    output_key="saving_capacity",
    tools=[load_bank_statement, estimate_affordability],
)

