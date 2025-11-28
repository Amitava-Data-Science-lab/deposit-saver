from google.genai import types
from google.adk.apps.app import EventsCompactionConfig

retry_config=types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504], # Retry on these HTTP errors
)

system_safety_settings = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            )
        ]

events_compaction_config=EventsCompactionConfig(
        compaction_interval=10,  # Trigger compaction every 10 new invocations.
        overlap_size=2          # Include last 2 invocation from the previous window.
    )