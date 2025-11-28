import logging
import os
import json
from fastapi import File, Form, UploadFile
from typing import Optional
from google.adk.runners import Runner
from google.adk.sessions import VertexAiSessionService , InMemorySessionService
from google.cloud import storage
from google.genai import types

# --- 1. Global Setup (Logging and GCS Client) ---

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('housing_goal_agent.log')
    ]
)
logger = logging.getLogger(__name__)

# GCS Client Initialization
GCS_BUCKET_NAME = os.getenv("GCS_BANK_DATA_BUCKET", "your-bank-data-staging-bucket")
storage_client = storage.Client()

# --- 2. Session Service Initialization ---

# Define the Agent Engine ID required by VertexAiSessionService
# VERTEX_AI_AGENT_ENGINE_ID = os.getenv("VERTEX_AI_AGENT_ENGINE_ID")
session_service = InMemorySessionService()
"""
if not VERTEX_AI_AGENT_ENGINE_ID:
    logger.error("VERTEX_AI_AGENT_ENGINE_ID environment variable is missing.")
    raise EnvironmentError("VERTEX_AI_AGENT_ENGINE_ID must be set for VertexAiSessionService.")

session_service = VertexAiSessionService(
    agent_engine_id=VERTEX_AI_AGENT_ENGINE_ID
)
logger.info(f"Initialized VertexAiSessionService with ID: {VERTEX_AI_AGENT_ENGINE_ID}")
"""

# 3. Initialize the Runner (Import orchestrator_agent from its module)
from src.agent.Orchestrator import orchestrator_agent 

runner = Runner(
    agent=orchestrator_agent,
    session_service=session_service,
    app_name="financial_orchestrator_app" # Required for scoping sessions
)

# --- Event Logging Helper Function ---
async def log_event(event):
    """Helper to log events during the agent's execution run."""
    logger.info(f"Event from Agent: {event.author}")
    
    calls = event.get_function_calls()
    if calls:
        for call in calls:
            tool_name = call.name
            arguments = call.args
            logger.info(f"  Tool Call: {tool_name}, Args: {arguments}")
    
    responses = event.get_function_responses()
    if responses:
        for response in responses:
            tool_name = response.name
            logger.info(f"  Tool Result: {tool_name} -> {response.response}")

    if event.is_final_response():
        if event.content and event.content.parts and event.content.parts[0].text:
            final_response_content = event.content.parts[0].text
            logger.info(f"<<< Agent '{event.author}' Final Response: {final_response_content}")
        else:
            logger.info("Final response is non-textual or empty.")

# --- 4. Instantiate the FastAPI App via the Runner (The Key Change) ---
# This initializes the FastAPI app, adds the runner's internal routes, 
# enables CORS, and serves the demo FE at the root path '/'.
app = FastApi()


# --- 5. Custom Endpoint for Chat and File Upload ---
@app.post("/process_user_turn/")
async def process_user_turn(
    user_input: str = Form(""), # Default to empty string if not provided
    user_id: str = Form(...),
    session_id: str = Form(...),
    uploaded_file: Optional[UploadFile] = File(None),
):
    logger.info(f"Received input from {user_id}: '{user_input}' for session {session_id}")

    file_reference_or_path = None
    bank_data_payload = {}
    
    if uploaded_file:
        # --- File Upload and GCS Storage ---
        mime_type = uploaded_file.content_type 
        destination_blob_name = f"{user_id}/{session_id}/{uploaded_file.filename}"
        
        try:
            bucket = storage_client.bucket(GCS_BUCKET_NAME)
            blob = bucket.blob(destination_blob_name)
            
            blob.upload_from_file(
                uploaded_file.file, 
                content_type=mime_type
            )
            
            file_reference_or_path = f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
            logger.info(f"File uploaded to: {file_reference_or_path}")

            bank_data_payload = {
                "file_path": file_reference_or_path,
                "mime_type": mime_type,
            }

        except Exception as e:
            logger.error(f"GCS Upload Error: {e}")
            return {
                "status": "error", 
                "session_id": session_id, 
                "agent_response": f"Failed to upload file to storage: {str(e)}"
            }

    # --- Construct Agent Input ---
    full_user_text = user_input
    if bank_data_payload:
        metadata_json = json.dumps(bank_data_payload)
        full_user_text = f"{user_input}\nFILE_METADATA: {metadata_json}" if user_input else f"FILE_METADATA: {metadata_json}"
    
    user_content = types.Content(
        role="user",
        parts=[types.Part(text=full_user_text)]
    )
    
    # --- 6. Run Agent and Process Stream ---
    assistant_reply_text = []

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content):
        await log_event(event)
        
        if event.author == "orchestrator_agent" and event.content and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "text", None):
                    assistant_reply_text.append(part.text)
    
    # --- 7. Final Return to Front-End (FE) ---
    if assistant_reply_text:
        full_reply = "".join(assistant_reply_text)
        return {
            "status": "success",
            "session_id": session_id,
            "agent_response": full_reply
        }
    else:
        return {
            "status": "error",
            "session_id": session_id,
            "agent_response": "Agent execution finished, but no final text response was generated."
        }

# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)