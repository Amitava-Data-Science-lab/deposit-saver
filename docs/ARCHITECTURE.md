# Deposit Saver - System Architecture

**Version 0.2**

This document provides a comprehensive technical overview of the Deposit Saver system architecture, including agent design, data flow, caching strategies, and integration patterns.

## Table of Contents

- [Overview](#overview)
- [High-Level Architecture](#high-level-architecture)
- [Agent Architecture](#agent-architecture)
- [Data Flow](#data-flow)
- [Caching Strategy](#caching-strategy)
- [State Management](#state-management)
- [Session Management](#session-management)
- [Tool Architecture](#tool-architecture)
- [Error Handling](#error-handling)
- [Evaluation Framework](#evaluation-framework)
- [Deployment Architecture](#deployment-architecture)

## Overview

The Deposit Saver is a multi-agent system built on Google's Agent Development Kit (ADK) that helps users plan and save for mortgage deposits. The system employs a hierarchical agent architecture with specialized agents coordinated by an orchestrator.

### Key Design Principles

1. **Separation of Concerns** - Each agent handles a specific domain
2. **Composability** - Agents can be combined and reused
3. **Stateful Conversations** - Session state persists across interactions
4. **Intelligent Caching** - Reduce API costs through GCS-based caching
5. **Deterministic Workflow** - State machine guides users through process
6. **Testability** - Comprehensive evaluation framework with test scenarios

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                  (FastAPI + REPL + REST API)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     Orchestrator Agent                          │
│              (Gemini 2.5 Flash, temp=0.0)                       │
│    - Conversational interface                                   │
│    - Agent coordination                                         │
│    - Workflow enforcement                                       │
└────┬────────┬────────┬────────┬────────┬─────────────────┬─────┘
     │        │        │        │        │                 │
     │        │        │        │        │                 │
┌────▼────┐ ┌▼─────┐ ┌▼────┐ ┌▼─────┐ ┌▼──────────┐ ┌────▼────────┐
│ Housing │ │ Bank │ │Risk │ │ Plan │ │ Workflow  │ │   Memory    │
│  Goal   │ │ Data │ │Prof.│ │ Gen. │ │  Router   │ │   Tool      │
└────┬────┘ └──────┘ └─────┘ └──────┘ └───────────┘ └─────────────┘
     │
     ├──► Property Price Agent (sub-agent)
     │
     └──► Tools Layer
          ├─► Postcode Validation (postcodes.io)
          ├─► Property Search (Google Search)
          ├─► House Price Cache (GCS)
          ├─► Financial Calculations
          └─► State Persistence
```

### Component Layers

1. **Presentation Layer** - FastAPI web interface, REPL chat, REST API
2. **Orchestration Layer** - Main orchestrator agent
3. **Agent Layer** - Specialized domain agents
4. **Tool Layer** - Reusable tools and utilities
5. **Data Layer** - GCS cache, SQLite sessions, state management
6. **External Services** - Google Search, postcodes.io, Vertex AI

## Agent Architecture

### Orchestrator Agent

**Location:** [src/agent/Orchestrator.py](../src/agent/Orchestrator.py)

**Purpose:** Main conversational interface and agent coordinator

**Configuration:**
- **Model:** `gemini-2.5-flash`
- **Temperature:** 0.0 (deterministic)
- **Max Tokens:** 10,000

**Responsibilities:**
1. Engage users in natural conversation
2. Coordinate specialized agents via tool calls
3. Enforce 4-step workflow with confirmation gates
4. Maintain session context
5. Provide user-friendly responses

**Tools:**
- `housing_goalagent` (AgentTool)
- `bank_data_agent` (AgentTool)
- `risk_profiler_agent` (AgentTool)
- `plan_generator_agent` (AgentTool)

**Workflow Stages:**
1. **Housing Goal Collection** - Gather property requirements
2. **Bank Data Analysis** - Analyze financial capacity
3. **Risk Profiling** - Assess investment tolerance
4. **Plan Generation** - Create savings plan

### Housing Goal Agent

**Location:** [src/agent/housinggoal.py](../src/agent/housinggoal.py)

**Purpose:** Validate postcodes and research property prices

**Configuration:**
- **Model:** `gemini-2.5-flash`
- **Temperature:** 0.2
- **Output Schema:** `HousingGoalState`

**Two-Phase Process:**

**Phase 1: Postcode Validation & Price Research**
1. Validate UK postcode format via `outcode_checker()`
2. Check cache with `load_house_price_from_gcs()`
3. If cache miss, delegate to Property Price Agent
4. Save results with `save_house_price_to_gcs()`
5. Present options to user

**Phase 2: Selection & Deposit Calculation**
1. User confirms property selection
2. Calculate deposit target (typically 10-15%)
3. Return structured output

**Tools:**
- `outcode_checker()` - Postcode validation
- `nearby_outcodes()` - Suggest alternatives
- `property_price_agent` - Property search sub-agent
- `load_house_price_from_gcs()` - Cache retrieval
- `save_house_price_to_gcs()` - Cache storage

**Output Schema:**
```python
{
    "status": "success",
    "postcode": "HP12",
    "property_type": "2-bed house",
    "min_price": 250000,
    "max_price": 350000,
    "deposit_target": 50000,
    "price_options": [...]
}
```

### Property Price Agent

**Location:** [src/agent/PropertyPriceAgent.py](../src/agent/PropertyPriceAgent.py)

**Purpose:** Sub-agent specialized for property price research

**Configuration:**
- **Model:** `gemini-2.5-flash`
- **Temperature:** 0.2
- **Output Schema:** `PropertyPriceOutput`

**Process:**
1. Receive postcode and property type
2. Call `property_price_search()` with Google Search
3. Extract structured price data from results
4. Return price ranges by property type with sources

**Tools:**
- `property_price_search()` - Google Search API integration

**Output Schema:**
```python
{
    "status": "success",
    "postcode": "HP12",
    "price_options": [
        {
            "property_type": "2-bed house",
            "min_price": 250000,
            "max_price": 350000,
            "source": "rightmove.co.uk"
        }
    ]
}
```

### Bank Data Agent

**Location:** [src/agent/BankData.py](../src/agent/BankData.py)

**Purpose:** Analyze bank statements to determine saving capacity

**Configuration:**
- **Model:** `gemini-2.5-flash`
- **Temperature:** 0.2
- **Output Schema:** `CapacityState`

**Process:**
1. Validate CSV format via `load_bank_statement()`
2. Calculate monthly income and expenses
3. Call `estimate_affordability()` with transaction data
4. Determine suggested monthly investment
5. Return capacity metrics

**Tools:**
- `load_bank_statement()` - CSV validation
- `estimate_affordability()` - Surplus calculation

**CSV Requirements:**
- Columns: `Transaction Date`, `Description`, `Credit amount`, `Debit amount`
- Minimum 3 months of data
- Valid numeric formatting

**Output Schema:**
```python
{
    "status": "success",
    "suggested_investment": 500,
    "avg_surplus": 600,
    "median_surplus": 550
}
```

### Risk Profiler Agent

**Location:** [src/agent/RiskProfiler.py](../src/agent/RiskProfiler.py)

**Purpose:** Assess user's risk tolerance and investment preferences

**Configuration:**
- **Model:** `gemini-2.5-flash`
- **Temperature:** 0.3
- **Output Schema:** `RiskProfileOutput`

**Process:**
1. Collect 3 risk assessment questions
   - Income stability (1-5 scale)
   - Time horizon (years)
   - Loss reaction (categorical)
2. Call `risk_classification()` to map to risk band
3. Determine max equity allocation
4. Return risk profile

**Tools:**
- `risk_classification()` - Maps responses to risk bands 1-4

**Risk Bands:**
- **Band 1:** Conservative (max 20% equity)
- **Band 2:** Moderate-Conservative (max 35% equity)
- **Band 3:** Moderate (max 50% equity)
- **Band 4:** Aggressive (max 70% equity)

**Output Schema:**
```python
{
    "status": "success",
    "risk_band": 2,
    "risk_band_text": "moderate",
    "max_equity_share": 0.5,
    "profile_summary": "Moderate risk tolerance..."
}
```

### Plan Generator Agent

**Location:** [src/agent/PlanGenerator.py](../src/agent/PlanGenerator.py)

**Purpose:** Create personalized savings and investment plans

**Configuration:**
- **Model:** `gemini-2.5-flash`
- **Temperature:** 0.3
- **Output Schema:** `PlanOutput`

**Process:**
1. Receive inputs: deposit target, capacity, risk profile, horizon
2. Call `feasibility_calculator()` to assess viability
3. Generate plan based on feasibility code
4. Provide alternatives for tight/infeasible scenarios
5. Return detailed plan

**Tools:**
- `feasibility_calculator()` - Plan viability assessment

**Feasibility Codes:**
- **FEASIBLE** - Plan achievable within timeframe
- **TIGHT** - Achievable but challenging
- **INFEASIBLE** - Not achievable with current parameters

**Output Schema:**
```python
{
    "status": "success",
    "monthly_savings": 400,
    "monthly_investment": 100,
    "total_monthly": 500,
    "time_horizon_years": 5,
    "feasibility": "feasible",
    "investment_strategy": "50% equity, 50% cash ISA"
}
```

### Workflow Router Agent

**Location:** [src/agent/WorkflowRouterAgent.py](../src/agent/WorkflowRouterAgent.py)

**Purpose:** Determine current workflow stage and next steps

**Configuration:**
- **Model:** `gemini-2.5-flash`
- **Temperature:** 0.2
- **Output Schema:** `WorkflowState`

**Process:**
1. Call `get_current_state()` to retrieve session state
2. Analyze completed stages
3. Determine current stage
4. Identify missing information
5. Return next steps

**Tools:**
- `get_current_state()` - State retrieval

**Workflow Stages:**
1. `start` - Initial state
2. `housing` - Postcode validation & property search
3. `capacity` - Bank statement analysis
4. `risk` - Risk profiling
5. `planning` - Plan generation
6. `done` - Completion

**Output Schema:**
```python
{
    "current_stage": "housing",
    "next_stage": "capacity",
    "completed_stages": ["start"],
    "missing_data": ["bank_statement"],
    "ready_for_planning": false
}
```

## Data Flow

### End-to-End User Journey

```
1. User Request
   └─► "I want to buy a 2-bed house in HP12"
        │
        ▼
2. Orchestrator Agent
   └─► Routes to Housing Goal Agent
        │
        ▼
3. Housing Goal Agent
   ├─► Validate postcode (postcodes.io)
   ├─► Check cache (GCS)
   │   └─► Cache miss
   ├─► Call Property Price Agent
   │   └─► Google Search API
   ├─► Save to cache (GCS)
   └─► Return price options
        │
        ▼
4. User Confirms Selection
   └─► "I'll go with the 2-bed house at £300k"
        │
        ▼
5. Housing Goal Agent
   └─► Calculate deposit (£30k at 10%)
   └─► Return HousingGoalState
        │
        ▼
6. Orchestrator Agent
   └─► Prompt for bank statement
        │
        ▼
7. User Uploads CSV
   └─► Bank Data Agent
        ├─► Validate CSV format
        ├─► Calculate monthly surplus
        ├─► Call estimate_affordability()
        └─► Return CapacityState
             │
             ▼
8. Orchestrator Agent
   └─► Ask risk questions
        │
        ▼
9. User Answers Questions
   └─► Risk Profiler Agent
        ├─► Collect responses
        ├─► Call risk_classification()
        └─► Return RiskProfileOutput
             │
             ▼
10. Orchestrator Agent
    └─► Generate plan
         │
         ▼
11. Plan Generator Agent
    ├─► Call feasibility_calculator()
    ├─► Generate savings/investment split
    └─► Return PlanOutput
         │
         ▼
12. Orchestrator Agent
    └─► Present plan to user
```

### Data Persistence Flow

```
Session State:
┌─────────────────┐
│  User Message   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Orchestrator   │──► InMemorySessionService
└────────┬────────┘      └─► SQLite (sessions.db)
         │
         ▼
┌─────────────────┐
│ Specialized     │──► Agent Output to Session State
│ Agent           │      └─► state[agent.output_key] = result
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ State Persister │──► StatePersisterTool
│ Tool            │      └─► Tracks workflow progression
└─────────────────┘

Cache Flow:
┌─────────────────┐
│ Housing Goal    │
│ Agent           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Check Cache     │──► load_house_price_from_gcs()
│ (GCS Bucket)    │      └─► Key: {postcode}_{property_type}.json
└────────┬────────┘
         │
    Cache Hit? ────Yes──► Return cached data
         │
         No
         │
         ▼
┌─────────────────┐
│ Property Price  │──► Google Search API
│ Agent           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Save to Cache   │──► save_house_price_to_gcs()
└─────────────────┘
```

## Caching Strategy

### House Price Cache

**Storage:** Google Cloud Storage (GCS)

**Cache Key Format:**
```
{postcode}_{property_type}.json
```

**Example:**
```
HP12_2-bed-house.json
HP11_3-bed-semi-detached.json
SW1A_1-bed-flat.json
```

**Cache Entry Structure:**
```json
{
    "postcode": "HP12",
    "property_type": "2-bed house",
    "min_price": 250000,
    "max_price": 350000,
    "price_options": [
        {
            "property_type": "2-bed house",
            "min_price": 250000,
            "max_price": 350000,
            "source": "rightmove.co.uk"
        }
    ],
    "timestamp": "2025-01-15T10:30:00Z",
    "search_results": "..."
}
```

**Cache Workflow:**

1. **Cache Lookup**
   ```python
   cached_data = load_house_price_from_gcs(postcode, property_type)
   if cached_data:
       return cached_data  # Cache hit
   ```

2. **Cache Miss**
   ```python
   # Call Property Price Agent
   search_results = property_price_agent.search(postcode, property_type)

   # Store in cache
   save_house_price_to_gcs(postcode, property_type, search_results)
   ```

**Benefits:**
- Reduces Google Search API costs
- Faster response times (sub-second vs. 3-5 seconds)
- Consistent data across sessions
- Reduces LLM token usage

**Cache Invalidation:**
- Currently: No automatic expiration
- Future: Consider TTL-based invalidation (e.g., 30 days)

## State Management

### Session State Schema

The session state tracks all collected information throughout the conversation:

```python
{
    # Housing Goal State
    "housing_goal_state": {
        "status": "success",
        "postcode": "HP12",
        "property_type": "2-bed house",
        "deposit_target": 30000
    },

    # Bank Data State
    "capacity_state": {
        "status": "success",
        "suggested_investment": 500,
        "avg_surplus": 600
    },

    # Risk Profile State
    "risk_profile_state": {
        "status": "success",
        "risk_band": 2,
        "max_equity_share": 0.5
    },

    # Plan State
    "plan_state": {
        "status": "success",
        "monthly_savings": 400,
        "monthly_investment": 100,
        "feasibility": "feasible"
    },

    # Workflow State
    "workflow_stage": "planning",
    "completed_stages": ["start", "housing", "capacity", "risk"],

    # User Preferences
    "user:preferences": {
        "preferred_property_type": "2-bed house",
        "risk_tolerance": "moderate"
    }
}
```

### State Persistence Tool

**Location:** [src/tools/StatePersisterTool.py](../src/tools/StatePersisterTool.py)

**Functions:**

1. **`get_current_state()`**
   - Reads session state
   - Analyzes completed stages
   - Determines workflow progression
   - Returns current workflow state

2. **`after_tool_store_state()`** (Callback)
   - Executes after each tool call
   - Stores agent outputs in session state
   - Updates workflow stage

3. **`clean_llm_json_output()`**
   - Cleans JSON output from LLM
   - Removes markdown code fences
   - Ensures valid JSON

### Workflow State Transitions

```
start ──► housing ──► capacity ──► risk ──► planning ──► done
  │          │           │          │          │
  │          │           │          │          └─► Plan generated
  │          │           │          └─► Risk profile collected
  │          │           └─► Bank statement analyzed
  │          └─► Property selected & deposit calculated
  └─► Initial conversation
```

**Transition Rules:**
1. Cannot skip stages
2. Must complete current stage before advancing
3. User confirmation required at each gate
4. Can revisit previous stages

## Session Management

### Dual Session Architecture

The system uses two different session management strategies:

#### 1. Main Orchestrator (Interactive Chat)

**File:** [main.py](../main.py)

**Session Service:** `InMemorySessionService()`

**Storage:** SQLite database (`sessions.db`)

**Usage:** REPL chat, local testing

**Configuration:**
```python
session_service = InMemorySessionService()
SESSION_SERVICE_URI = "sqlite:///./sessions.db"

runner = Runner(
    agent=orchestrator_agent,
    app_name="housing_deposit_planner",
    session_service=session_service
)
```

**Session Lifecycle:**
1. Create session: `session_service.create_session()`
2. Run agent: `runner.run_async()`
3. Store state: Automatic via session service
4. Retrieve state: `session_service.get_session()`

#### 2. Root Agent (Evaluation)

**File:** [mortgage_deposit_agent/agent.py](../mortgage_deposit_agent/agent.py)

**Session Service:** `InMemorySessionService()` (builder pattern)

**Memory Service:** `InMemoryMemoryService()`

**Tools:** `PreloadMemoryTool()`

**Usage:** Google ADK evaluation framework

**Configuration:**
```python
def session_service_builder():
    return InMemorySessionService()

def memory_service_builder():
    return InMemoryMemoryService()

root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='mortgage_deposit_agent',
    tools=[
        agent_tool.AgentTool(agent=housing_goalagent),
        agent_tool.AgentTool(agent=bank_data_agent),
        agent_tool.AgentTool(agent=risk_profiler_agent),
        agent_tool.AgentTool(agent=plan_generator_agent),
        PreloadMemoryTool()  # Memory management
    ]
)
```

### FastAPI Integration

**Base URL:** `http://localhost:8080`

**Key Endpoints:**
```python
# Get FastAPI app
app = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri="sqlite:///./sessions.db",
    allow_origins=["*"],
    web=True,
    trace_to_cloud=True
)

# Endpoints:
# GET  /                  - Web interface
# GET  /docs              - OpenAPI documentation
# GET  /health            - Health check
# POST /agents/{agent_name}/sessions/{session_id}/messages
```

**Example Request:**
```bash
curl -X POST "http://localhost:8080/agents/mortgage_deposit_agent/sessions/SESSION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "I want to buy a 2-bed house in HP12"}'
```

## Tool Architecture

### Tool Categories

1. **Financial Tools** ([FinancialTools.py](../src/tools/FinancialTools.py))
2. **Web Search Tools** ([WebSearch.py](../src/tools/WebSearch.py))
3. **File Tools** ([FileLoadTool.py](../src/tools/FileLoadTool.py))
4. **Cache Tools** ([HousePriceCache.py](../src/tools/HousePriceCache.py))
5. **State Tools** ([StatePersisterTool.py](../src/tools/StatePersisterTool.py))

### Tool Implementation Pattern

All tools follow the Google ADK tool pattern:

```python
from google.adk.tools import Tool

@Tool
def my_tool(param1: str, param2: int) -> dict:
    """
    Tool description that the LLM uses to understand when to call this tool.

    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2

    Returns:
        Dictionary with result containing status and data
    """
    try:
        # Tool implementation
        result = perform_operation(param1, param2)

        return {
            "status": StatusCodes.SUCCESS.value,
            "data": result
        }
    except Exception as e:
        return {
            "status": StatusCodes.ERROR.value,
            "error_code": ErrorCode.SOME_ERROR.value,
            "message": str(e)
        }
```

### Financial Tools

**Location:** [src/tools/FinancialTools.py](../src/tools/FinancialTools.py)

#### `estimate_affordability()`

**Purpose:** Calculate monthly surplus from bank statement data

**Inputs:**
- `csv_content`: Bank statement CSV string
- `house_price`: Target property price

**Process:**
1. Parse CSV with pandas
2. Calculate monthly income (credits)
3. Calculate monthly expenses (debits)
4. Compute surplus: `income - expenses`
5. Apply affordability rules

**Output:**
```python
{
    "status": "success",
    "suggested_investment": 500,
    "avg_surplus": 600,
    "median_surplus": 550,
    "comfortable_range": [450, 550]
}
```

#### `deposit_calculator()`

**Purpose:** Calculate required deposit amount

**Inputs:**
- `house_price`: Property price
- `deposit_percentage`: Default 10%

**Output:**
```python
{
    "deposit_amount": 30000,
    "house_price": 300000,
    "percentage": 10
}
```

#### `feasibility_calculator()`

**Purpose:** Assess plan viability

**Inputs:**
- `target_deposit`: Required deposit
- `horizon_years`: Time horizon
- `current_savings`: Existing savings
- `monthly_capacity`: Monthly investment capacity

**Logic:**
```python
required_monthly = (target_deposit - current_savings) / (horizon_years * 12)

if required_monthly <= monthly_capacity * 0.8:
    return "FEASIBLE"
elif required_monthly <= monthly_capacity:
    return "TIGHT"
else:
    return "INFEASIBLE"
```

**Output:**
```python
{
    "feasibility_code": "FEASIBLE",
    "required_monthly": 417,
    "available_monthly": 500,
    "shortfall": 0
}
```

#### `risk_classification()`

**Purpose:** Map risk responses to standardized risk bands

**Inputs:**
- `income_stability`: 1-5 scale
- `time_horizon_years`: Years
- `loss_reaction`: Categorical response

**Mapping Logic:**
```python
score = (income_stability * 0.3) +
        (min(time_horizon_years / 10, 1) * 0.3) +
        (loss_reaction_score * 0.4)

if score < 0.3: risk_band = 1  # Conservative
elif score < 0.5: risk_band = 2  # Moderate-Conservative
elif score < 0.7: risk_band = 3  # Moderate
else: risk_band = 4  # Aggressive
```

**Output:**
```python
{
    "risk_band": 2,
    "risk_band_text": "moderate-conservative",
    "max_equity_share": 0.35,
    "description": "..."
}
```

### Web Search Tools

**Location:** [src/tools/WebSearch.py](../src/tools/WebSearch.py)

#### `outcode_checker()`

**Purpose:** Validate UK postcode via postcodes.io API

**API:** `https://api.postcodes.io/outcodes/{outcode}/validate`

**Process:**
1. Extract outcode (first part of postcode)
2. Call postcodes.io API
3. Return validation result

**Output:**
```python
{
    "status": "success",
    "valid": true,
    "outcode": "HP12"
}
```

#### `property_price_search()`

**Purpose:** Search for property prices using Google Search

**Inputs:**
- `postcode`: UK postcode
- `property_type`: Property type (e.g., "2-bed house")

**Process:**
1. Construct search query
2. Call Google Search API
3. Return raw search results for LLM extraction

**Output:**
```python
{
    "status": "success",
    "search_results": "...",  # Raw HTML/text
    "query": "HP12 2-bed house prices"
}
```

#### `nearby_outcodes()`

**Purpose:** Find nearby postcodes for invalid outcode

**API:** `https://api.postcodes.io/outcodes/{outcode}/nearest`

**Output:**
```python
{
    "status": "success",
    "nearby_outcodes": ["HP11", "HP13", "HP10"]
}
```

### Cache Tools

**Location:** [src/tools/HousePriceCache.py](../src/tools/HousePriceCache.py)

#### `save_house_price_to_gcs()`

**Purpose:** Store property price data in GCS

**Inputs:**
- `postcode`: UK postcode
- `property_type`: Property type
- `price_data`: Price data to cache

**Process:**
1. Construct blob name: `{postcode}_{property_type}.json`
2. Serialize to JSON
3. Upload to GCS bucket
4. Set metadata (timestamp, content-type)

**GCS Configuration:**
```python
BUCKET_NAME = os.getenv("HOUSE_PRICE_BUCKET")
```

#### `load_house_price_from_gcs()`

**Purpose:** Retrieve cached property price data

**Inputs:**
- `postcode`: UK postcode
- `property_type`: Property type

**Process:**
1. Construct blob name
2. Check if blob exists
3. Download and deserialize JSON
4. Return data or None

**Output:**
```python
{
    "status": "success",
    "cached": true,
    "data": { ... }
}
```

### File Tools

**Location:** [src/tools/FileLoadTool.py](../src/tools/FileLoadTool.py)

#### `load_bank_statement()`

**Purpose:** Validate and load CSV bank statement

**Required Columns:**
- `Transaction Date`
- `Description`
- `Credit amount`
- `Debit amount`

**Validation:**
1. Check file exists
2. Verify CSV format
3. Validate required columns
4. Check minimum 3 months data
5. Verify numeric formatting

**Output:**
```python
{
    "status": "success",
    "csv_content": "...",
    "row_count": 150,
    "date_range": "2024-01-01 to 2024-04-30"
}
```

## Error Handling

### Error Code System

**Location:** [src/tools/ErrorAndStatus.py](../src/tools/ErrorAndStatus.py)

All error codes are defined as enums for consistency:

#### StatusCodes
```python
class StatusCodes(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
```

#### HousingErrorCode
```python
class HousingErrorCode(str, Enum):
    INVALID_POSTCODE = "invalid_postcode"
    POSTCODE_NOT_FOUND = "postcode_not_found"
    NO_PROPERTIES_FOUND = "no_properties_found"
    SEARCH_API_ERROR = "search_api_error"
    CACHE_ERROR = "cache_error"
```

#### BankFileErrorCode
```python
class BankFileErrorCode(str, Enum):
    FILE_NOT_FOUND = "file_not_found"
    INVALID_CSV_FORMAT = "invalid_csv_format"
    MISSING_COLUMNS = "missing_columns"
    INSUFFICIENT_DATA = "insufficient_data"
    INVALID_NUMERIC_FORMAT = "invalid_numeric_format"
```

#### FeasibilityCode
```python
class FeasibilityCode(str, Enum):
    FEASIBLE = "feasible"
    TIGHT = "tight"
    INFEASIBLE = "infeasible"
```

### Error Response Pattern

All tools return structured error responses:

```python
{
    "status": "error",
    "error_code": "invalid_postcode",
    "message": "The postcode 'XYZ' is not a valid UK postcode",
    "suggestions": ["HP12", "HP11", "HP13"]
}
```

### Error Propagation

```
Tool Error
    │
    ▼
Agent catches error
    │
    ▼
Agent returns structured error in output schema
    │
    ▼
Orchestrator receives error state
    │
    ▼
Orchestrator asks user for correction
```

## Evaluation Framework

### Architecture

**Location:** [tests/test_eval_agent.py](../tests/test_eval_agent.py)

**Framework:** Google ADK `AgentEvaluator`

**Evaluation Datasets:** [Scripts/evals/](../Scripts/evals/)

### Evaluation Flow

```
1. Load Evalset
   └─► JSON file with conversation turns
        │
        ▼
2. AgentEvaluator
   ├─► Create session per evaluation
   ├─► Replay user messages
   ├─► Capture agent responses
   └─► Compare with expected outputs
        │
        ▼
3. Metrics Calculation
   ├─► tool_trajectory_avg_score
   └─► response_match_score
        │
        ▼
4. Results Storage
   └─► tests/results/
        ├─► Metrics JSON
        ├─► Response comparison
        └─► Tool call logs
```

### Evalset Structure

**Format:** JSON with multi-turn conversations

```json
{
    "turns": [
        {
            "user": "I want to buy a 2-bed house in HP12",
            "expected_tools": ["housing_goalagent"],
            "expected_response_contains": ["postcode", "property prices"]
        },
        {
            "user": "I'll go with the 2-bed house at £300k",
            "expected_tools": ["deposit_calculator"],
            "expected_response_contains": ["deposit", "£30,000"]
        }
    ]
}
```

### Session Recording

**Script:** [Scripts/convert_session_to_eval.py](../Scripts/convert_session_to_eval.py)

**Process:**
1. Record live conversation session
2. Save to `Scripts/sessions/session-{uuid}.json`
3. Convert to evalset format
4. Save to `Scripts/evals/evalset_{name}.evalset.json`

**Benefits:**
- Real user interactions become test cases
- Regression testing
- Performance benchmarking

## Deployment Architecture

### Local Development

```
┌─────────────────────────────────────────┐
│         Developer Machine               │
│                                         │
│  ┌───────────────────────────────┐     │
│  │      main.py (FastAPI)        │     │
│  │  - Orchestrator Agent         │     │
│  │  - InMemorySessionService     │     │
│  │  - SQLite (sessions.db)       │     │
│  └───────────┬───────────────────┘     │
│              │                          │
│              ▼                          │
│  ┌───────────────────────────────┐     │
│  │  Specialized Agents           │     │
│  │  - Housing Goal               │     │
│  │  - Bank Data                  │     │
│  │  - Risk Profiler              │     │
│  │  - Plan Generator             │     │
│  └───────────┬───────────────────┘     │
│              │                          │
│              ▼                          │
│  ┌───────────────────────────────┐     │
│  │  External Services            │     │
│  │  - Gemini API (via API key)   │     │
│  │  - postcodes.io               │     │
│  │  - Google Search              │     │
│  └───────────────────────────────┘     │
└─────────────────────────────────────────┘
```

### Cloud Deployment (Vertex AI)

```
┌──────────────────────────────────────────────────────────┐
│                   Google Cloud Platform                  │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │     Vertex AI Agent Engines                    │     │
│  │  - Autoscaling (0-10 instances)                │     │
│  │  - Managed environment                         │     │
│  │  - Built-in monitoring                         │     │
│  └────────────┬───────────────────────────────────┘     │
│               │                                          │
│               ▼                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │     Secret Manager                             │     │
│  │  - GOOGLE_API_KEY_SECRET                       │     │
│  │  - FIREBASE_SECRET                             │     │
│  └────────────────────────────────────────────────┘     │
│               │                                          │
│               ▼                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  Cloud Storage (GCS)                           │     │
│  │  - HOUSE_PRICE_BUCKET                          │     │
│  │  - Property price cache                        │     │
│  └────────────────────────────────────────────────┘     │
│               │                                          │
│               ▼                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  Cloud Logging & Monitoring                    │     │
│  │  - OpenTelemetry tracing                       │     │
│  │  - Cloud Trace                                 │     │
│  │  - Error Reporting                             │     │
│  └────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────┘
```

### Deployment Process

**Script:** [deploy_remote.py](../deploy_remote.py)

**Steps:**
1. Build container with Dockerfile
2. Push to Google Container Registry
3. Deploy to Vertex AI Agent Engines
4. Configure autoscaling
5. Set environment variables
6. Enable monitoring

**Configuration:**
```python
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
HOUSE_PRICE_BUCKET = os.getenv("HOUSE_PRICE_BUCKET")
```

## Performance Considerations

### Latency Optimization

1. **Property Price Caching**
   - Cache hit: ~200ms
   - Cache miss: ~3-5s (Google Search + LLM)
   - Reduction: 93% for cached queries

2. **Agent Temperature Settings**
   - Orchestrator: 0.0 (deterministic, faster)
   - Housing Goal: 0.2 (balance speed/creativity)
   - Plan Generator: 0.3 (more creative for alternatives)

3. **Token Optimization**
   - Output schemas reduce token usage
   - Focused prompts minimize unnecessary generation
   - History summarization for long conversations

### Scalability

1. **Stateless Agents**
   - Agents are stateless
   - State stored in session service
   - Horizontal scaling possible

2. **Caching Layer**
   - GCS provides distributed caching
   - Reduces load on search APIs
   - Scales with request volume

3. **Session Management**
   - SQLite for local development
   - Vertex AI Session Service for production
   - Supports concurrent users

## Security Architecture

### API Key Management

```
┌─────────────────────────────────────┐
│    Application Code                 │
│  (No hardcoded secrets)             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Environment Variables (.env)       │
│  - GOOGLE_API_KEY_SECRET (path)     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Google Cloud Secret Manager        │
│  - DEMO-ACCOUNT_API-KEY (value)     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Secret Manager Client              │
│  - Retrieves at runtime             │
│  - Cached in memory                 │
└─────────────────────────────────────┘
```

### Input Validation

1. **Postcode Validation**
   - UK postcode format regex
   - API validation via postcodes.io
   - Prevents injection attacks

2. **CSV Validation**
   - Column name checking
   - Data type validation
   - Size limits
   - Sanitization of user input

3. **Session Isolation**
   - Each user gets unique session ID
   - State isolated per session
   - No cross-session data leakage

### Data Privacy

1. **Bank Statement Data**
   - Processed in memory only
   - Not stored permanently
   - Deleted after session ends

2. **Session Data**
   - Stored in SQLite with session ID
   - No PII in logs
   - Can be cleared on demand

3. **Cache Data**
   - Only property price data cached
   - No user-specific information
   - Public market data only

## Future Architecture Enhancements

### Planned Improvements

1. **Cache TTL**
   - Add expiration to cached property prices
   - Automatic refresh after 30 days

2. **Async Tool Execution**
   - Parallel tool calls where possible
   - Reduce total latency

3. **Advanced Memory Management**
   - Conversation summarization
   - Long-term user preferences
   - Cross-session context

4. **Enhanced Evaluation**
   - A/B testing framework
   - Performance benchmarks
   - User satisfaction metrics

5. **Multi-Region Support**
   - Expand beyond UK postcodes
   - International property markets
   - Currency conversion

---

**Document Version:** 0.2
**Last Updated:** 2025-01-15
**Maintained By:** Development Team
