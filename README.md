# Deposit Saver - Mortgage Deposit Planning Agent

**Version 0.2**

An intelligent AI-powered agent system built with Google's Agent Development Kit (ADK) to help users plan and save for their mortgage deposit. The system analyzes housing goals, financial capacity, and risk profiles to generate personalized savings plans with optimized investment strategies.

## Overview

The Deposit Saver uses a multi-agent architecture orchestrated by Google's ADK (Agent Development Kit) and powered by Gemini 2.5 Flash to provide comprehensive mortgage deposit planning:

- **Housing Goal Analysis**: Validate UK postcodes and research property market prices with intelligent caching
- **Financial Capacity Assessment**: Analyze bank statements to determine realistic saving capacity
- **Risk Profiling**: Assess user's risk tolerance and map to investment strategies
- **Plan Generation**: Create personalized savings and investment plans with feasibility analysis
- **Workflow Routing**: Intelligently guide users through the multi-step planning process
- **Property Price Caching**: Cache property searches in Google Cloud Storage to reduce redundant API calls
- **Comprehensive Evaluation**: Built-in evaluation framework with test scenarios

## Architecture

The system uses a multi-agent architecture with specialized agents coordinated by an orchestrator:

```
┌─────────────────────────────────────────────┐
│          Orchestrator Agent                 │
│  (Coordinates workflow & user interaction)  │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴───────┬───────────┬──────────┬──────────────┐
       │               │           │          │              │
┌──────▼─────┐ ┌──────▼─────┐ ┌───▼─── ┐ ┌────▼────┐ ┌──────▼────────┐
│  Housing   │ │    Bank    │ │  Risk  │ │  Plan   │ │     Plan      │
│    Goal    │ │    Data    │ │Profiler│ │Generator│ │    Writer     │
│   Agent    │ │   Agent    │ │ Agent  │ │  Agent  │ │     Agent     │
└─────┬──────┘ └────────────┘ └─────── ┘ └─────────┘ └───────────────┘
      │
      ├─► Property Price Agent (sub-agent for web search)
      └─► House Price Cache (GCS storage)
```

### Core Agents

1. **Housing Goal Agent** ([housinggoal.py](src/agent/housinggoal.py))
   - Validates UK postcodes via postcodes.io API
   - Checks property price cache (GCS) before web search
   - Delegates to Property Price Agent for market research
   - Suggests nearby postcodes if invalid
   - Calculates deposit targets based on user selection

2. **Property Price Agent** ([PropertyPriceAgent.py](src/agent/PropertyPriceAgent.py))
   - Sub-agent specialized for property price research
   - Uses Google Search API for real-time market data
   - Extracts structured price data from search results
   - Returns prices by property type with sources

3. **Bank Data Agent** ([BankData.py](src/agent/BankData.py))
   - Validates CSV bank statement format
   - Analyzes transactions to calculate monthly surplus
   - Determines realistic saving capacity
   - Requires minimum 3 months of data

4. **Risk Profiler Agent** ([RiskProfiler.py](src/agent/RiskProfiler.py))
   - Collects 3 risk assessment questions (1-5 scale)
   - Maps responses to risk bands (1-4: conservative to aggressive)
   - Recommends maximum equity allocation
   - Uses risk classification tool for standardized mapping

5. **Plan Generator Agent** ([PlanGenerator.py](src/agent/PlanGenerator.py))
   - Combines housing goals, capacity, and risk profile
   - Calls feasibility calculator to assess plan viability
   - Generates optimized savings and investment plans
   - Provides alternatives for tight or infeasible scenarios

6. **Workflow Router Agent** ([WorkflowRouterAgent.py](src/agent/WorkflowRouterAgent.py))
   - Determines current workflow stage (start → housing → capacity → risk → planning → done)
   - Identifies missing information
   - Returns next steps based on session state
   - Pure state retrieval (no calculations)

7. **Orchestrator Agent** ([Orchestrator.py](src/agent/Orchestrator.py))
   - Main conversational interface with users
   - Coordinates all specialized agents
   - 4-step process with confirmation gates
   - Maintains session state and context

## Features

### Core Functionality
- **Conversational AI Interface** - Powered by Gemini 2.5 Flash for natural interactions
- **Multi-Agent Orchestration** - Specialized agents coordinated by Google ADK
- **UK Postcode Validation** - Real-time validation via postcodes.io API
- **Property Price Research** - Google Search integration with intelligent caching
- **Bank Statement Analysis** - CSV transaction analysis with surplus calculation
- **Risk Assessment** - Standardized risk profiling with 4 risk bands
- **Feasibility Analysis** - Plan viability assessment with alternatives
- **Personalized Savings Plans** - Investment strategies based on time horizon and risk

### Technical Features
- **Property Price Caching** - GCS-based caching to reduce redundant API calls
- **Session State Management** - SQLite-based persistence for conversation continuity
- **Workflow State Machine** - Deterministic routing through planning stages
- **Error Handling** - Comprehensive error codes and status tracking
- **FastAPI Web Interface** - REST API with OpenAPI documentation
- **Evaluation Framework** - Google ADK evaluator with test scenarios
- **Session Recording** - Conversation logging for evaluation dataset creation
- **Memory Management** - PreloadMemoryTool for efficient context handling
- **Cloud Deployment** - Vertex AI Agent Engines support
- **Observability** - Structured logging and OpenTelemetry tracing

## Prerequisites

- Python 3.9+
- Google Cloud Project with Vertex AI enabled
- Google API Key (for Gemini models)
- Google Cloud Secret Manager access (for production)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd deposit-saver
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Environment Configuration

Create a `.env` file with the following variables:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Google API Key for Vertex AI Express Mode (Secret Manager path)
GOOGLE_API_KEY_SECRET=projects/PROJECT_ID/secrets/SECRET_NAME

# House Price Cache Bucket (GCS)
HOUSE_PRICE_BUCKET=your-house-price-cache-bucket

# Enable Vertex AI for Google GenAI
GOOGLE_GENAI_USE_VERTEXAI=True

# Firebase Configuration (Optional)
FIREBASE_SECRET_PROJECT_ID=your-firebase-project-id
FIREBASE_SECRET_NAME=firebase-config-secret
FIREBASE_SECRET_VERSION=latest

# Vertex AI Configuration (Optional)
VERTEX_AI_AGENT_ENGINE_ID=your-agent-engine-id
GCS_BANK_DATA_BUCKET=your-bank-data-bucket

# Mode (local or production)
MODE=local
```

See [.env.example](.env.example) for complete configuration details.

## Usage

### Running Locally

#### 1. Interactive Chat Mode

Run the orchestrator in conversational mode:

```bash
python main.py
```

This starts a REPL-style chat interface:

```
You: I want to buy a 2-bed house in HP12
Orchestrator: I'll help you plan for that! Let me research property prices in HP12...
```

Type `quit` or `exit` to end the conversation.

#### 2. FastAPI Web Interface

Start the web server:

```bash
python main.py
```

The server runs on `http://localhost:8080` by default. Access the API at:
- `/` - Web interface
- `/docs` - OpenAPI documentation
- `/health` - Health check endpoint

#### 3. Testing Individual Agents

```python
import asyncio
from main import test_housing_goal_agent
import json

# Test housing goal agent
query = {"query": "Give me a plan for buying a 2-bed house in HP12"}
asyncio.run(test_housing_goal_agent(json.dumps(query)))
```

### Deployment

#### Deploy to Vertex AI

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

Quick deployment:

```bash
python deploy_remote.py
```

This deploys the agent to Vertex AI Agent Engines with:
- Autoscaling (0-10 instances)
- Managed environment with all dependencies
- Built-in monitoring and tracing
- Production-ready configuration

## Project Structure

```
deposit-saver/
├── main.py                      # Entry point, FastAPI app, test harness
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment configuration template
├── Dockerfile                   # Container configuration
├── deploy.py                    # Local deployment script
├── deploy_remote.py             # Vertex AI deployment script
│
├── mortgage_deposit_agent/      # Root agent package (evaluation endpoint)
│   ├── agent.py                 # Root agent with PreloadMemoryTool
│   ├── evalset41eab2.evalset.json  # Evaluation dataset
│   └── __init__.py
│
├── src/
│   ├── agent/                   # Specialized agents
│   │   ├── Orchestrator.py      # Main coordinator (used by main.py)
│   │   ├── housinggoal.py       # Housing goal agent
│   │   ├── PropertyPriceAgent.py # Property price search sub-agent
│   │   ├── BankData.py          # Bank data analyzer
│   │   ├── RiskProfiler.py      # Risk assessment
│   │   ├── PlanGenerator.py     # Plan generation
│   │   ├── WorkflowRouterAgent.py # Workflow state routing
│   │   ├── AgentFactory.py      # Agent registration
│   │   ├── FinancialInstrument.py # Vertex AI Search integration
│   │   └── schema.py            # Pydantic data models
│   │
│   ├── Prompts/                 # Agent system prompts
│   │   ├── OrchestratorPrompt.py
│   │   ├── HousingGoalPrompt.py
│   │   ├── PropertyPricePrompt.py
│   │   ├── BankDataPrompt.py
│   │   ├── RiskProfilerPrompt.py
│   │   ├── PlanGeneratorPrompt.py
│   │   ├── WorkFlowRouterPrompt.py
│   │   └── user_output_format.py
│   │
│   ├── tools/                   # Agent tools
│   │   ├── FileLoadTool.py      # CSV validation
│   │   ├── FinancialTools.py    # Financial calculations
│   │   ├── WebSearch.py         # Postcode & property search
│   │   ├── HousePriceCache.py   # GCS caching
│   │   ├── StatePersisterTool.py # State management
│   │   ├── ErrorAndStatus.py    # Error code enums
│   │   └── utils.py             # Configuration & utilities
│   │
│   ├── api/                     # FastAPI definitions
│   │   └── app.py
│   │
│   └── auth/                    # Authentication
│       ├── auth.py
│       └── secret_manager.py
│
├── Scripts/
│   ├── convert_session_to_eval.py  # Session to evalset converter
│   ├── evals/                   # Evaluation datasets
│   │   ├── evalset_complete_happypath.evalset.json
│   │   ├── evalset_Affordable_Property_Iteration.evalset.json
│   │   └── evalset_postcode_error.evalset.json
│   ├── sessions/                # Recorded test sessions
│   │   └── session-*.json       # Session recordings
│   └── others/
│       └── GenerateBankStatements.py  # Synthetic data generator
│
├── data/                        # Sample/test data
│   ├── bankstatement.csv        # Original example
│   ├── bankstatement_50k.csv    # 50k income variant
│   ├── bankstatement_60k.csv    # 60k income variant
│   ├── bankstatement_75k.csv    # 75k income variant
│   ├── bankstatement_100k.csv   # 100k income variant
│   └── savings_deposit.csv      # Financial products data
│
├── tests/                       # Test suite
│   ├── test_eval_agent.py       # Evaluation runner
│   └── results/                 # Evaluation outputs
│
└── docs/                        # Documentation
    └── DEPLOYMENT.md            # Deployment guide
```

## Data Models

### HousingGoalState
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

### CapacityState
```python
{
    "status": "success",
    "suggested_investment": 500,
    "avg_surplus": 600,
    "median_surplus": 550
}
```

### RiskProfileOutput
```python
{
    "status": "success",
    "risk_band": 2,
    "risk_band_text": "moderate",
    "max_equity_share": 0.5,
    "profile_summary": "Moderate risk tolerance..."
}
```

## Tools and Technologies

- **Google ADK** (Agent Development Kit) - Multi-agent orchestration framework
- **Google Gemini 2.5 Flash** - LLM for agent intelligence
- **FastAPI** - Web framework for API endpoints
- **Vertex AI** - Cloud deployment and scaling
- **Pydantic** - Data validation and schema management
- **Pandas** - Data analysis for bank statements
- **Google Cloud Secret Manager** - Secure credential storage
- **OpenTelemetry** - Observability and tracing

## Bank Statement Format

The system expects CSV bank statements with the following columns:
- `Transaction Date` - Transaction date
- `Description` - Transaction description
- `Credit amount` - Incoming funds (deposits, income)
- `Debit amount` - Outgoing funds (expenses, withdrawals)

**Requirements:**
- Minimum 3 months of transaction data
- CSV format with header row
- Valid numeric values for amounts

**Sample Data:**
- [data/bankstatement.csv](data/bankstatement.csv) - Original example
- [data/bankstatement_50k.csv](data/bankstatement_50k.csv) - £50k annual income
- [data/bankstatement_60k.csv](data/bankstatement_60k.csv) - £60k annual income
- [data/bankstatement_75k.csv](data/bankstatement_75k.csv) - £75k annual income
- [data/bankstatement_100k.csv](data/bankstatement_100k.csv) - £100k annual income

Generate custom bank statements using:
```bash
python Scripts/others/GenerateBankStatements.py
```

## Evaluation & Testing

### Running Evaluations

The project includes a comprehensive evaluation framework using Google ADK's AgentEvaluator:

```bash
# Run all evaluation tests
pytest tests/test_eval_agent.py

# Run specific evaluation scenario
pytest tests/test_eval_agent.py -k "happy_path"
```

### Evaluation Datasets

Located in [Scripts/evals/](Scripts/evals/):

1. **evalset_complete_happypath.evalset.json** (68KB)
   - End-to-end happy path scenario
   - User successfully completes all stages: housing → bank → risk → plan
   - Tests 3-bed house search in HP11 postcode

2. **evalset_Affordable_Property_Iteration.evalset.json** (68KB)
   - Property selection iteration scenarios until a affordable choice is found.
   - Tests multiple property types and user preference confirmation
   - Validates agent's ability to handle changing requirements

3. **evalset_postcode_error.evalset.json** (3.5KB)
   - Error handling scenario
   - Tests invalid postcode validation and nearby suggestions

### Creating Evaluation Datasets from Sessions

Record a conversation session, then convert it to an evaluation dataset:

```bash
# Convert recorded session to evalset
python Scripts/convert_session_to_eval.py

# Session files are stored in Scripts/sessions/
# Generated evalsets are compatible with Google ADK evaluator
```

### Evaluation Metrics

The evaluator uses:
- `tool_trajectory_avg_score` - Measures tool call accuracy
- `response_match_score` - Measures response quality

Results are stored in [tests/results/](tests/results/).

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_eval_agent.py
```

### Adding a New Agent

1. Create agent file in `src/agent/`
2. Define agent prompt in `src/Prompts/`
3. Define input/output schemas in `src/agent/schema.py`
4. Register agent in orchestrator's tools list
5. Add to `src/agent/AgentFactory.py` if needed
6. Create evaluation dataset for the agent

### Custom Tools

Create tools in `src/tools/` and register with agents:

```python
from google.adk.tools import Tool

@Tool
def my_custom_tool(param: str) -> dict:
    """Tool description that the LLM will use to understand when to call this tool.

    Args:
        param: Description of the parameter

    Returns:
        Dictionary with result
    """
    # Tool implementation
    return {"result": "..."}
```

### Error Codes

All error codes are defined in [src/tools/ErrorAndStatus.py](src/tools/ErrorAndStatus.py):

- `StatusCodes` - Success/error statuses
- `HousingErrorCode` - Postcode validation errors
- `BankFileErrorCode` - CSV validation errors
- `FeasibilityCode` - Plan feasibility statuses
- `CommonErrorCodes` - General error codes

## Key Features Deep Dive

### Property Price Caching System

The system implements intelligent caching to reduce API calls and improve performance:

**How it works:**
1. Housing Goal Agent checks cache before web search
2. Cache key: `{postcode}_{property_type}.json`
3. Cache storage: Google Cloud Storage bucket
4. Cache hit: Returns stored data instantly
5. Cache miss: Calls Property Price Agent → stores result in GCS

**Benefits:**
- Reduces Google Search API costs
- Faster response times for repeated queries
- Consistent data across sessions

**Implementation:**
- [src/tools/HousePriceCache.py](src/tools/HousePriceCache.py)
- `save_house_price_to_gcs()` - Stores search results
- `load_house_price_from_gcs()` - Retrieves cached data

### Workflow State Machine

The application uses a deterministic state machine to guide users through the planning process:

**Stages:**
1. `start` - Initial state
2. `housing` - Postcode validation & property search
3. `capacity` - Bank statement analysis
4. `risk` - Risk profiling questionnaire
5. `planning` - Plan generation
6. `done` - Completion

**State Management:**
- [src/tools/StatePersisterTool.py](src/tools/StatePersisterTool.py)
- `get_current_state()` - Returns current workflow stage
- Workflow Router Agent determines next steps
- Orchestrator enforces confirmation gates between stages

### Dual Agent Architecture

The project uses two orchestrator agents for different purposes:

**1. Main Orchestrator** ([src/agent/Orchestrator.py](src/agent/Orchestrator.py))
- Used by [main.py](main.py) for interactive chat
- REPL-style conversation interface
- InMemorySessionService for local testing

**2. Root Agent** ([mortgage_deposit_agent/agent.py](mortgage_deposit_agent/agent.py))
- Entry point for Google ADK evaluation framework
- Uses PreloadMemoryTool for memory management
- InMemoryMemoryService for agent memory
- Designed for automated testing and evaluation

Both coordinate the same specialized agents but with different session management strategies.

## Security

- **API Keys** - Stored in Google Cloud Secret Manager, never in code
- **Environment Variables** - Configuration via `.env` file (not committed)
- **Service Account Authentication** - For Google Cloud resource access
- **Input Validation** - CSV format validation, postcode validation
- **Error Handling** - Comprehensive error codes prevent information leakage
- **`.gitignore`** - Configured to exclude sensitive files, credentials, and session data

## Monitoring and Logging

### Local Logging
- Structured logging to `housing_goal_agent.log`
- Log levels: DEBUG, INFO, WARNING, ERROR
- Includes agent interactions, tool calls, and state transitions

```bash
# View real-time logs
tail -f housing_goal_agent.log

# Filter by agent
grep "housing_goal_agent" housing_goal_agent.log
```

### Cloud Logging (Vertex AI Deployment)
- OpenTelemetry integration for distributed tracing
- Cloud Trace for request visualization
- Automatic error reporting

```bash
# View cloud logs
gcloud logging tail "resource.type=aiplatform_agent_engine"

# Filter by severity
gcloud logging read "severity>=ERROR" --limit 50
```

### Session State Persistence
- SQLite database: `sessions.db`
- Stores conversation history and agent outputs
- Enables session resumption and analysis

### Evaluation Results
- Stored in [tests/results/](tests/results/)
- Includes metrics, trajectories, and comparison data

## Troubleshooting

### Common Issues

**Import errors**: Ensure all dependencies installed
```bash
pip install -r requirements.txt
```

**API key issues**: Verify Secret Manager access
```bash
gcloud secrets describe DEMO-ACCOUNT_API-KEY --project=PROJECT_ID
```

**Session issues**: Clear session database
```bash
rm sessions.db
```

**Cache issues**: Clear GCS cache bucket
```bash
gsutil rm -r gs://HOUSE_PRICE_BUCKET/**
```

**Postcode validation failures**:
- Ensure UK postcode format (e.g., "HP12", "SW1A")
- Check postcodes.io API availability
- Review error codes in logs

**CSV validation errors**:
- Verify column names: `Transaction Date`, `Description`, `Credit amount`, `Debit amount`
- Ensure minimum 3 months of data
- Check for proper numeric formatting

**Evaluation test failures**:
```bash
# Clean test results
rm -rf tests/results/*

# Re-run evaluations
pytest tests/test_eval_agent.py -v
```

## API Reference

### Root Agent Endpoint

The root agent is exposed via Google ADK's FastAPI integration:

**Base URL:** `http://localhost:8080` (local) or your deployed Vertex AI URL

**Key Endpoints:**
- `GET /` - Web interface
- `GET /docs` - Interactive OpenAPI documentation
- `GET /health` - Health check endpoint
- `POST /agents/{agent_name}/sessions/{session_id}/messages` - Send message to agent

**Example Request:**
```bash
curl -X POST "http://localhost:8080/agents/mortgage_deposit_agent/sessions/SESSION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I want to buy a 2-bed house in HP12"
  }'
```

### Agent Tools Reference

All tools are documented in their respective files:

- **Financial Tools** - [src/tools/FinancialTools.py](src/tools/FinancialTools.py)
  - `estimate_affordability()`, `deposit_calculator()`, `feasibility_calculator()`, `risk_classification()`

- **Web Search Tools** - [src/tools/WebSearch.py](src/tools/WebSearch.py)
  - `outcode_checker()`, `property_price_search()`, `nearby_outcodes()`

- **File Tools** - [src/tools/FileLoadTool.py](src/tools/FileLoadTool.py)
  - `load_bank_statement()`

- **Cache Tools** - [src/tools/HousePriceCache.py](src/tools/HousePriceCache.py)
  - `save_house_price_to_gcs()`, `load_house_price_from_gcs()`

- **State Tools** - [src/tools/StatePersisterTool.py](src/tools/StatePersisterTool.py)
  - `get_current_state()`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests and evaluation datasets
5. Ensure all tests pass (`pytest tests/`)
6. Update documentation
7. Submit a pull request

**Development Guidelines:**
- Follow existing code structure and patterns
- Add type hints to all functions
- Document all new tools and agents
- Create evaluation datasets for new features
- Update README.md with new functionality

## Version History

### Version 0.2 (Current)
- Added Property Price Caching system with GCS integration
- Implemented Property Price Agent as sub-agent
- Added comprehensive evaluation framework
- Enhanced error handling with standardized error codes
- Added workflow state machine with routing agent
- Created multiple bank statement test data variants
- Improved session recording and conversion to evalsets
- Added dual agent architecture for testing vs. production

### Version 0.1 (Initial)
- Basic multi-agent architecture
- Housing goal, bank data, risk profiler, and plan generator agents
- FastAPI web interface
- Vertex AI deployment support

## License

[Add your license information here]

## Support

For issues and questions:
- Check [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for deployment help
- Review `housing_goal_agent.log` for error details
- Verify environment configuration in `.env`
- Check evaluation results in `tests/results/`

## Acknowledgments

Built with:
- **Google Agent Development Kit (ADK)** - Multi-agent orchestration framework
- **Google Gemini 2.5 Flash** - Large language model powering all agents
- **Google Cloud Platform** - Infrastructure and services (Vertex AI, GCS, Secret Manager)
- **FastAPI** - Modern web framework for API endpoints
- **Pydantic** - Data validation and schema management
- **Pandas** - Financial data analysis
