# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import LlmAgent
from google.adk.tools import VertexAiSearchTool
from src.tools.utils import system_safety_settings
from google.genai import types

# Replace with your Vertex AI Search Datastore ID, and respective region (e.g. us-central1 or global).
# Format: projects/<PROJECT_ID>/locations/<REGION>/collections/default_collection/dataStores/<DATASTORE_ID>
DATASTORE_PATH = "projects/capstone-project-479414/locations/us/collections/default_collection/dataStores/savings-deposits-and-cash-isa_1764277019724"


# Tool Instantiation
# You MUST provide your datastore ID here.
vertex_search_tool = VertexAiSearchTool(data_store_id=DATASTORE_PATH)

# Agent Definition
financial_instrument_agent = LlmAgent(
    name="financial_instrument_Agent",
    model="gemini-2.0-flash", # Requires Gemini model
    tools=[vertex_search_tool],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,  # More deterministic output
        max_output_tokens=8000,
        safety_settings=system_safety_settings
    ),
    instruction=f"""You are a helpful financial advisor who answers questions based on information found in the document store: {DATASTORE_PATH}.
    Use the search tool to find relevant information before answering.
    If the answer isn't in the documents, say that you couldn't find the information.
    """,
    description="Answers questions using a specific Vertex AI Search datastore.",
)
