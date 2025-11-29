import logging
from google.adk.agents import LlmAgent
from google.genai import types
from src.tools.StatePersisterTool import get_current_state
from src.Prompts.WorkFlowRouterPrompt import system_prompt
from src.tools.utils import system_safety_settings
from src.agent.schema import WorkflowState, SessionState



logger = logging.getLogger(__name__)


logger.info("workflow_router_agent")

workflow_router_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='workflow_router_agent',
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,  # More deterministic output
        max_output_tokens=8000,
        safety_settings=system_safety_settings
    ),
    description="""Based on the current state determine the next step in the process.""",
    instruction= system_prompt,
    input_schema=SessionState,
    output_key="workflow_state",
    tools=[get_current_state],
)