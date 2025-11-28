import logging
from google.adk.agents import LlmAgent
from google.genai import types
from src.tools.FinancialTools import deposit_calculator
from src.tools.utils import retry_config
from src.tools.WebSearch import property_price_search
from src.Prompts.HousingGoalPrompt import system_prompt
from pydantic import BaseModel, Field
from src.tools.utils import system_safety_settings

logger = logging.getLogger(__name__)

class LLMAgentFactory:
    def __init__(self, agent_name, model='gemini-2.5-flash', temperature=0, max_output_tokens=250):
        self.agents = {}

    def register_agent(self, agent_name: str, agent: LlmAgent):
        self.agents[agent_name] = agent

    def get_agent(self, agent_name: str) -> LlmAgent:
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not registered.")
        return self.agents[agent_name]
