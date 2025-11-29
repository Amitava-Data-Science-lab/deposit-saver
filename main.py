import logging
from src.agent.housinggoal import housing_goalagent
from src.agent.BankData import bank_data_agent
from src.agent.RiskProfiler import risk_profiler_agent
from src.agent.PlanGenerator import plan_generator_agent
from src.agent.Orchestrator import orchestrator_agent
from google.adk.runners import Runner
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.sessions import  VertexAiSessionService, InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
import json
import uuid
import asyncio
import os
from dotenv import load_dotenv

import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

# Load environment variables
load_dotenv()

# Clean up any previous logs
for log_file in ["housing_goal_agent.log"]:
    if os.path.exists(log_file):
        os.remove(log_file)
        print(f"🧹 Cleaned up {log_file}")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('housing_goal_agent.log')
    ]
)

logger = logging.getLogger(__name__)

# Helper function to get API key from Secret Manager
def get_api_key_from_secret(secret_path: str) -> str:
    """
    Retrieve API key from Google Cloud Secret Manager.

    Args:
        secret_path: Full secret path (e.g., 'projects/PROJECT_ID/secrets/SECRET_NAME')

    Returns:
        API key string
    """
    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()

    # Add /versions/latest if not already in path
    if "/versions/" not in secret_path:
        secret_path = f"{secret_path}/versions/latest"

    try:
        response = client.access_secret_version(name=secret_path)
        api_key = response.payload.data.decode('UTF-8')
        logger.info(f"Successfully retrieved API key from secret: {secret_path.split('/secrets/')[1].split('/versions')[0]}")
        return api_key
    except Exception as e:
        logger.error(f"Failed to retrieve API key from {secret_path}: {e}")
        raise

# --- 1. Define Constants ---
mode = os.getenv("MODE", "local")
USER_ID = "test_user_456"
APP_NAME = "housing_deposit_planner"
SESSION_ID = str(uuid.uuid4())
session_service = InMemorySessionService()
# Initialize Vertex AI Session Service
# Read configuration from environment variables
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "capstone-project-479414")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_API_KEY_SECRET = os.getenv("GOOGLE_API_KEY_SECRET", "projects/485422000664/secrets/DEMO-ACCOUNT_API-KEY")

logger.info(f"Initializing Vertex AI Session Service with project: {GOOGLE_CLOUD_PROJECT}, location: {GOOGLE_CLOUD_LOCATION}")

# Retrieve API key from Secret Manager
"""
express_mode_api_key = get_api_key_from_secret(GOOGLE_API_KEY_SECRET)

session_service = VertexAiSessionService(
    # project=GOOGLE_CLOUD_PROJECT,
    # location=GOOGLE_CLOUD_LOCATION,
    express_mode_api_key=express_mode_api_key
)
# artifact_service = InMemoryArtifactService()
"""
####
# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

#
# Vertex AI Session Service URI for FastAPI integration
#SESSION_SERVICE_URI = f"vertexai://{GOOGLE_CLOUD_PROJECT}/{GOOGLE_CLOUD_LOCATION}"
SESSION_SERVICE_URI = "sqlite:///./sessions.db"
# Example allowed origins for CORS
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8080", "*"]
# Set web=True if you intend to serve a web interface, False otherwise
SERVE_WEB_INTERFACE = True

# Call the function to get the FastAPI app instance
# Ensure the agent directory name ('capital_agent') matches your agent folder
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
    trace_to_cloud=True
)


async def test_housing_goal_agent(query:str):
    runner = Runner(agent=housing_goalagent,
                    app_name=APP_NAME,
                    session_service=session_service)

    await call_agent_and_log( runner, housing_goalagent, SESSION_ID, query)

async def test_bank_data_agent(bank_data_payload:str):
    runner = Runner(agent=bank_data_agent,
                    app_name=APP_NAME,
                    session_service=session_service)
    await call_agent_and_log(runner, bank_data_agent, SESSION_ID, bank_data_payload)


async def test_risk_profiler_agent(risk_payload:str):
    runner = Runner(agent=risk_profiler_agent,
                    app_name=APP_NAME,
                    session_service=session_service)
    await call_agent_and_log(runner, risk_profiler_agent, SESSION_ID, risk_payload)
    
async def test_plan_generator_agent(plan_payload:str):
    runner = Runner(agent=plan_generator_agent,
                    app_name=APP_NAME,
                    session_service=session_service)
    await call_agent_and_log(runner, plan_generator_agent, SESSION_ID, plan_payload)
    

async def call_agent_and_log(
    runner_instance: Runner,
    agent_instance: LlmAgent,
    session_id: str,
    query_json: str
):
    """Sends a query to the specified agent/runner and prints results."""
    logger.info(f"\n>>> Calling Agent: '{agent_instance.name}' | Query: {query_json}")

    user_content = types.Content(role='user', parts=[types.Part(text=query_json)])

    final_response_content = "No final response received."
    async for event in runner_instance.run_async(user_id=USER_ID, session_id=session_id, new_message=user_content):
        logger.info(f"Event from Agent  : {event.author}")
        calls = event.get_function_calls()
        if calls:
            for call in calls:
                tool_name = call.name
                arguments = call.args # This is usually a dictionary
                logger.info(f"  Tool: {tool_name}, Args: {arguments}")
        
        responses = event.get_function_responses()
        if responses:
            for response in responses:
                tool_name = response.name
                result_dict = response.response # The dictionary returned by the tool
                logger.info(f"  Tool Result: {tool_name} -> {result_dict}")


        if event.is_final_response():
            logger.info(f"Final response received. for Agent: {agent_instance.name}")
            if event.content and event.content.parts and event.content.parts[0].text:
                # For output_schema, the content is the JSON string itself
                final_response_content = event.content.parts[0].text
                logger.info(f"<<< Agent '{agent_instance.name}' Response: {final_response_content}")
            elif event.actions and event.actions.skip_summarization and event.get_function_responses():
               # Handle displaying the raw tool result if needed
               response_data = event.get_function_responses()[0].response
               logger.info(f"Display raw tool result: {response_data}")
            elif hasattr(event, 'long_running_tool_ids') and event.long_running_tool_ids:
               logger.info("Display message: Tool is running in background...")
            else:
               # Handle other types of final responses if applicable
               logger.info("Display: Final non-textual response or signal.")

    

    current_session = await session_service.get_session(app_name=APP_NAME,
                                                  user_id=USER_ID,
                                                  session_id=session_id)
    stored_output = current_session.state.get(agent_instance.output_key)

    # Pretty print if the stored output looks like JSON (likely from output_schema)
    logger.info(f"--- Session State ['{agent_instance.output_key}']: -------")
    try:
        # Attempt to parse and pretty print if it's JSON
        parsed_output = json.loads(stored_output)
        logger.info(json.dumps(parsed_output, indent=2))
    except (json.JSONDecodeError, TypeError):
         # Otherwise, print as string
        logger.info(stored_output)
    print("-" * 30)

async def log_event(event):
    logger.info(f"Event from Agent  : {event.author}")
    calls = event.get_function_calls()
    if calls:
        for call in calls:
            tool_name = call.name
            arguments = call.args # This is usually a dictionary
            logger.info(f"  Tool: {tool_name}, Args: {arguments}")
    
    responses = event.get_function_responses()
    if responses:
        for response in responses:
            tool_name = response.name
            result_dict = response.response # The dictionary returned by the tool
            logger.info(f"  Tool Result: {tool_name} -> {result_dict}")


    if event.is_final_response():
        logger.info(f"Final response received. for Agent: {event.author}")
        if event.content and event.content.parts and event.content.parts[0].text:
            # For output_schema, the content is the JSON string itself
            final_response_content = event.content.parts[0].text
            logger.info(f"<<< Agent '{event.author}' Response: {final_response_content}")
        elif event.actions and event.actions.skip_summarization and event.get_function_responses():
            # Handle displaying the raw tool result if needed
            response_data = event.get_function_responses()[0].response
            logger.info(f"Display raw tool result: {response_data}")
        elif hasattr(event, 'long_running_tool_ids') and event.long_running_tool_ids:
            logger.info("Display message: Tool is running in background...")
        else:
            # Handle other types of final responses if applicable
            logger.info("Display: Final non-textual response or signal.")


async def main():
    
    #####---------- Run Housing Goal Agent -------------###############
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    housing_query = {
        "query:": "Give me a plan for buying a 2-bed house in HP12"
    }
    # await test_housing_goal_agent(json.dumps(housing_query))
    
    bank_data_payload = {
        "file_path": "./data/bankstatement.csv",
        "mime_type": "text/csv",
    }
    # await test_bank_data_agent(json.dumps(bank_data_payload))

    risk_payload = {
        "income_stability": 4,
        "time_horizon_years": 5,
        "loss_reaction": "uncomfortable_but_okay"
        }
    # await test_risk_profiler_agent(json.dumps(risk_payload))

    plan_payload  = {
        "target_deposit": 20000,
        "horizon_years": 5,
        "current_savings": 0,
        "capacity": {
            "suggested_savings": 190,
            "comfortable_saving_range": [190, 210]
        },
        "risk_profile": {
            "risk_band": "moderate",
            "max_equity_share": 0.5
        }
    }

    # await test_plan_generator_agent(json.dumps(plan_payload))

    await run_orchestrator_chat(orchestrator_agent, session_service)



async def run_orchestrator_chat(orchestrator_agent, session_service, app_name: str = "housing_deposit_planner"):
    USER_ID = "test_user"
    SESSION_ID = str(uuid.uuid4())
    
    logger.info(f"Starting orchestrator session. Session ID: {SESSION_ID}, User ID: {USER_ID}")

    # Create session
    await session_service.create_session(
        app_name=app_name,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    runner = Runner(
        agent=orchestrator_agent,
        app_name=app_name,
        session_service=session_service,
    )

    # Simple REPL-style loop
    while True:
        user_input = input("\nYou: ")
        if user_input.lower().strip() in {"quit", "exit"}:
            ## TODO Summarize teh conversation and store in memory
            print("Exiting conversation.")
            break

        user_content = types.Content(
            role="user",
            parts=[types.Part(text=user_input)]
        )

        assistant_reply_text = []

        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=user_content,
        ):
            # Stream assistant messages as they arrive
            if event.content and event.content.parts:
                await log_event(event)
                if event.author == "orchestrator_agent":
                    for part in event.content.parts:
                        if getattr(part, "text", None):
                            assistant_reply_text.append(part.text)

        if assistant_reply_text:
            full_reply = "".join(assistant_reply_text)
            print(f"\nOrchestrator: {full_reply}")
        else:
            print("\nOrchestrator: (no response)")

        # Optional: access and inspect session state from your session_service here
        # state = await session_service.get_session_state(app_name, USER_ID, SESSION_ID)
        # logger.debug(f"Current session state: {state}")



if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8080
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
