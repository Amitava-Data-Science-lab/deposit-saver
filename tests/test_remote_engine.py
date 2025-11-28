
from vertexai import agent_engines

RESOURCE_ID = "projects/485422000664/locations/us-central1/reasoningEngines/4226676628798832640"
async def main():
    try:
        
        remote_app = agent_engines.get(RESOURCE_ID)
        print(remote_app.name)
        remote_session = await remote_app.async_create_session(user_id="u_456")
        print(remote_session)

        async for event in remote_app.async_stream_query(
            user_id="u_456",
            session_id=remote_session["id"],
            message="whats the weather in new york",
        ):
            print(event)
    
    except Exception as e:
        print(e)


if __name__ == "__main__":
    import asyncio   
    asyncio.run(main())

