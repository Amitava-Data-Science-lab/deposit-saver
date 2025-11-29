import logging
from google.adk.tools import ToolContext, FunctionTool
from typing import Any, Dict
from src.agent.schema import SessionState, WorkflowState, HousingGoalState, CapacityState, RiskProfileOutput, PlanOutput



logger = logging.getLogger(__name__)

import re

def clean_llm_json_output(raw_output: str) -> str:
    """Removes common LLM formatting wrappers (like ```json) from output."""
    
    if not raw_output:
        return "{}"
    
    # 1. Remove optional surrounding whitespace
    cleaned_output = raw_output.strip()
    
    # 2. Use a regular expression to strip the leading and trailing markers:
    # This pattern handles '```json', '```JSON', or just '```' 
    # optionally followed by any whitespace, both at the start and end.
    cleaned_output = re.sub(r'^\s*```(?:json|JSON)?\s*', '', cleaned_output)
    cleaned_output = re.sub(r'\s*```\s*$', '', cleaned_output)
    
    return cleaned_output
  

def get_current_state(state: SessionState)-> WorkflowState:
    logger.info("=== Getting current workflow state ===")
        
    workflow_state = WorkflowState()
   

    if state == None:
        workflow_state.current_stage = "housing"
        workflow_state.next_stage_to_address = "housing"
        workflow_state.data_items_required_to_complete = ["postcode", "property_type"]
        workflow_state.notes = "Get the initial data for housing_goal_agent"
        return workflow_state
     
    
    if state.stage == None or state.stage == "start":        
        logger.info(f"Stage is {state.stage}, setting current_stage to 'housing'")
        workflow_state.current_stage = "housing"
        workflow_state.next_stage_to_address = "housing"
        workflow_state.data_items_required_to_complete = ["postcode", "property_type"]
        workflow_state.notes = "Get the initial data for housing_goal_agent"
        return workflow_state
    else:
        workflow_state.current_stage = state.stage
        logger.info(f"Current stage set to: {state.stage}")

    if state.stage == "housing":
        logger.info("Processing housing state")
        if state.housing_goal and state.housing_goal.status == "success":
            logger.debug(f"Housing goal found with success status: {state.housing_goal}")
            workflow_state.data_items_required_to_complete = []
            ## Check for critical Data elements for which input is needed
            if state.housing_goal.postcode == None:
                workflow_state.data_items_required_to_complete.append("postcode")
                logger.debug("Missing: postcode")
            if state.housing_goal.property_type == None:
                workflow_state.data_items_required_to_complete.append("property_type")
                logger.debug("Missing: property_type")
            if state.housing_goal.house_price == None:
                workflow_state.data_items_required_to_complete.append("house_price")
                logger.debug("Missing: house_price")
            if state.housing_goal.deposit_target == None:
                workflow_state.data_items_required_to_complete.append("deposit_target")
                logger.debug("Missing: deposit_target")
            if workflow_state.data_items_required_to_complete == []:
                workflow_state.notes = "Housing step is complete. Can proceed to next stage."
                workflow_state.next_stage_to_address = "capacity"
                logger.info("Housing step complete, moving to capacity stage")
            else:
                workflow_state.notes = "Housing is missing some required data"
                logger.warning(f"Housing missing data: {workflow_state.data_items_required_to_complete}")
        elif state.housing_goal and state.housing_goal.status == "AWAITING_CONFIRMATION":
             workflow_state.notes = "Keep in current state until Human confirmation is received"
             logger.info("Housing goal awaiting confirmation")
    elif state.stage == "capacity":
        logger.info("Processing capacity state")
        if state.bank_capacity and state.bank_capacity.status == "success":
                workflow_state.data_items_required_to_complete = []
                workflow_state.notes = "Capacity step is complete"
                logger.info("Capacity step complete")
    elif state.stage == "risk":
        logger.info("Processing risk state")
        if state.risk_profile and state.risk_profile.status == "success":
                    workflow_state.data_items_required_to_complete = []
                    workflow_state.notes = "Risk step is complete"
                    logger.info("Risk step complete")
    elif state.stage == "planning":
        logger.info("Processing planning state")
        if state.final_plan:
                    workflow_state.data_items_required_to_complete = []
                    workflow_state.notes = "Planning step is complete"
                    logger.info("Planning step complete")

    logger.info(f"Workflow state result: current_stage={workflow_state.current_stage}, notes={workflow_state.notes}")
    logger.debug(f"Full workflow state: {workflow_state}")
    return workflow_state


async def after_tool_store_state(tool, args, tool_context, tool_response):
    logger.info(f"After tool callback initiated for tool: {getattr(tool, 'name', 'unknown')}")
    state = tool_context.state
    logger.debug(f"Tool args: {args}")

       
    # Detect if this tool is an AgentTool and has an output_key
    output_key = None
    if hasattr(tool, "agent") and getattr(tool.agent, "output_key", None):
        output_key = tool.agent.output_key
        logger.info(f"Agent tool detected with output_key: {output_key}")

    if not output_key:
        # Tool doesn't have an output key → nothing to persist
        logger.info("No output key found, skipping preference storage")
        return None

    # Read the agent-as-tool output
    agent_output = state.get(output_key)
    agent_output = clean_llm_json_output(agent_output)
    logger.info(f"Agent output: {agent_output}")
    if agent_output is None:
        logger.info(f"No output found for key '{output_key}', skipping preference storage")
        return None
    
    session_state = SessionState()
    state_data = state.get("user:preferences", {})
    if state_data:
        session_state = SessionState.model_validate_json(state_data)
    
    ## Use the agent output and output key to populate the correct session state
    if tool.agent.name == "housing_goal_agent":
        session_state.housing_goal = HousingGoalState.model_validate_json(agent_output)
        session_state.stage = "housing"
    elif tool.agent.name == "bank_data_agent":
        session_state.bank_capacity = CapacityState.model_validate_json(agent_output)
        session_state.stage = "capacity"
    elif tool.agent.name == "risk_profiler_agent":
        session_state.risk_profile = RiskProfileOutput.model_validate_json(agent_output)
        session_state.stage = "risk"
    elif tool.agent.name == "plan_generator_agent":
        session_state.final_plan = PlanOutput.model_validate_json(agent_output)
        session_state.stage = "planning"

        
    logger.info(f"Storing agent output for: {tool.agent.name}")

    # Update user preferences    
    state_data = session_state.model_dump_json()
    state["user:preferences"] = state_data
    logger.info(f"Successfully stored preferences {state_data} for agent: {tool.agent.name}")
   
    return None

            
        

    


    
    



