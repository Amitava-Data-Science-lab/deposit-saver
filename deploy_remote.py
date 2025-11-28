import os
import sys
import asyncio
from dotenv import load_dotenv
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService

# Load environment variables from .env file
load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# Ensure the project root is at the beginning of the Python path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# print(sys.path)

import vertexai
from vertexai import agent_engines
from mortgage_deposit_agent.agent import root_agent

# Set defaults for environment variables if not in .env
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "capstone-project-479414")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
os.environ.setdefault("GOOGLE_CLOUD_STAGING_BUCKET", "gs://capstone-project-479414-staging")
# Define the regional host for Vertex AI
print(f"Project:, {os.environ["GOOGLE_CLOUD_PROJECT"]}")
print(f"Location:, {os.environ["GOOGLE_CLOUD_LOCATION"]}")
print(f"Staging Bucket:, {os.environ["GOOGLE_CLOUD_STAGING_BUCKET"]}")
print(f"Use Vertex AI:, {os.environ["GOOGLE_GENAI_USE_VERTEXAI"]}")

"""
def session_service_builder():

  return VertexAiSessionService()

def memory_service_builder():
  
  return VertexAiMemoryBankService()
"""

vertexai.init(
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location="us-central1",
    staging_bucket=os.environ["GOOGLE_CLOUD_STAGING_BUCKET"]

)

agent_app = agent_engines.AdkApp(agent=root_agent
             , app_name="mortgage_deposit_agent"
             , enable_tracing=True
             )

# Prepare environment variables for the deployed agent
env_vars = {
    "GOOGLE_CLOUD_PROJECT": os.environ["GOOGLE_CLOUD_PROJECT"],
    "GOOGLE_CLOUD_LOCATION": os.environ["GOOGLE_CLOUD_LOCATION"],
    "GOOGLE_GENAI_USE_VERTEXAI": os.environ["GOOGLE_GENAI_USE_VERTEXAI"],
    "GOOGLE_CLOUD_STAGING_BUCKET": os.environ["GOOGLE_CLOUD_STAGING_BUCKET"],
    # Firebase configuration
    # "FIREBASE_SECRET_PROJECT_ID": os.getenv("FIREBASE_SECRET_PROJECT_ID", "485422000664"),
    # "FIREBASE_SECRET_NAME": os.getenv("FIREBASE_SECRET_NAME", "capstone-project-firebase-config"),
    # "FIREBASE_SECRET_VERSION": os.getenv("FIREBASE_SECRET_VERSION", "latest"),
    # Google API Key for Vertex AI Express Mode
    # "GOOGLE_API_KEY_SECRET": os.getenv("GOOGLE_API_KEY_SECRET", "projects/485422000664/secrets/DEMO-ACCOUNT_API-KEY"),
}

print(f"\nEnvironment variables to be set in deployed agent:")
for key, value in env_vars.items():
    # Mask sensitive values for display
    display_value = value if "SECRET" not in key else f"{value[:30]}..." if len(value) > 30 else "***"
    print(f"  {key}: {display_value}")

remote_app = agent_engines.create(
    agent_engine=agent_app,
    display_name="mortgage_deposit_agent",
    requirements=[
        "google-cloud-aiplatform[adk,agent_engines]",
        "google-genai",
        "pydantic==2.12.4",
        "cloudpickle==3.1.2",
        "pandas",
        "google-cloud-storage",
        "google-cloud-secret-manager",
        "requests",
        "python-dotenv",
        "uvicorn[standard]",
        "fastapi",
        "opentelemetry-instrumentation-google-genai"
    ],
    extra_packages=["src", "mortgage_deposit_agent"],
    env_vars=env_vars,  # Pass environment variables to deployed agent
    min_instances=0,
    max_instances=10,
    resource_limits={"cpu": "2", "memory": "2Gi"}
)

print(f"Deployment finished!")
print(f"Resource Name: {remote_app.resource_name}")
