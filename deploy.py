import os
import sys
import asyncio

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# Ensure the project root is at the beginning of the Python path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# print(sys.path)

import vertexai
from vertexai import agent_engines
from mortgage_deposit_agent.agent import root_agent, session_service_builder, memory_service_builder


os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "capstone-project-479414")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
os.environ.setdefault("GOOGLE_CLOUD_STAGING_BUCKET", "gs://capstone-project-479414-staging")


vertexai.init(
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ["GOOGLE_CLOUD_LOCATION"],
    staging_bucket=os.environ["GOOGLE_CLOUD_STAGING_BUCKET"],
)

agent_app = agent_engines.AdkApp(agent=root_agent
             , session_service_builder=session_service_builder
             , memory_service_builder=memory_service_builder
             , enable_tracing=True
             )

async def main():
    session = await agent_app.async_create_session(user_id="user_123")
    print(session)

# Run the asynchronous main function 👈 REQUIRED!
if __name__ == "__main__":
    # This runs the 'main' async function using Python's event loop
    asyncio.run(main())

"""

remote_app = agent_engines.create(app=agent_app
                         , project=os.environ["GOOGLE_CLOUD_PROJECT"]
                         , location=os.environ["GOOGLE_CLOUD_LOCATION"],
                         # Define required Python packages for your agent to run
                        requirements=[
                            "google-cloud-aiplatform[adk,agent_engines]",
                            "google-genai"
                        ],
                        # Optional: Configure runtime resource controls
                        config={ 
                            "min_instances": 1, 
                            "max_instances": 10,
                            "resource_limits": {"cpu": "2", "memory": "2Gi"} 
                            }
                        )
"""

