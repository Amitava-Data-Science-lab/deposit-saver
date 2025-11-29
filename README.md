# Deposit Saver - Mortgage Deposit Planning Agent

An intelligent AI-powered agent system built with Google's Agent Development Kit (ADK) to help users plan and save for their mortgage deposit. The system analyzes housing goals, financial capacity, and risk profiles to generate personalized savings plans.

## Overview

The Deposit Saver uses a multi-agent architecture orchestrated by Google's ADK (Agent Development Kit) and powered by Gemini models to provide comprehensive mortgage deposit planning:

- **Housing Goal Analysis**: Understand user's property requirements and research market prices
- **Financial Capacity Assessment**: Analyze bank statements to determine realistic saving capacity
- **Risk Profiling**: Assess user's risk tolerance and investment preferences
- **Plan Generation**: Create personalized savings and investment plans
- **Workflow Routing**: Intelligently guide users through the planning process

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
│  Housing   │ │    Bank    │ │  Risk  │ │  Plan   │ │   Workflow    │
│    Goal    │ │    Data    │ │Profiler│ │Generator│ │    Router     │
│   Agent    │ │   Agent    │ │ Agent  │ │  Agent  │ │     Agent     │
└────────────┘ └────────────┘ └─────── ┘ └─────────┘ └───────────────┘
```

### Core Agents

1. **Housing Goal Agent** ([housinggoal.py](src/agent/housinggoal.py))
   - Captures user's property requirements (location, type, bedrooms)
   - Searches for property prices using web tools
   - Calculates deposit targets based on market data

2. **Bank Data Agent** ([BankData.py](src/agent/BankData.py))
   - Analyzes bank statement CSV files
   - Calculates monthly income and expenses
   - Determines realistic saving capacity

3. **Risk Profiler Agent** ([RiskProfiler.py](src/agent/RiskProfiler.py))
   - Assesses user's risk tolerance through questionnaire
   - Maps responses to risk bands (conservative, moderate, aggressive)
   - Recommends maximum equity allocation

4. **Plan Generator Agent** ([PlanGenerator.py](src/agent/PlanGenerator.py))
   - Combines housing goals, capacity, and risk profile
   - Generates optimized savings plans
   - Suggests investment strategies based on time horizon

5. **Workflow Router Agent** ([WorkflowRouterAgent.py](src/agent/WorkflowRouterAgent.py))
   - Determines current stage of user journey
   - Identifies missing information
   - Routes to appropriate next steps

6. **Orchestrator Agent** ([Orchestrator.py](src/agent/Orchestrator.py))
   - Main conversational interface with users
   - Coordinates all specialized agents
   - Maintains session state and context

## Features

- Conversational AI interface powered by Gemini 2.5 Flash
- Multi-agent workflow orchestration
- Bank statement analysis (CSV format)
- Real-time property price research via web search
- Risk assessment and profiling
- Personalized savings plan generation
- Session state management with persistence
- FastAPI web interface
- Google Cloud deployment support (Vertex AI)
- Comprehensive logging and tracing

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
GOOGLE_CLOUD_STAGING_BUCKET=gs://your-staging-bucket

# API Keys
GOOGLE_API_KEY_SECRET=projects/PROJECT_ID/secrets/SECRET_NAME

# Firebase (Optional)
FIREBASE_SECRET_PROJECT_ID=your-firebase-project-id
FIREBASE_SECRET_NAME=firebase-config-secret
FIREBASE_SECRET_VERSION=latest

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
├── deploy_remote.py            # Vertex AI deployment script
│
├── mortgage_deposit_agent/     # Main agent package
│   ├── agent.py                # Root orchestrator agent
│   └── __init__.py
│
├── src/
│   ├── agent/                  # Specialized agents
│   │   ├── Orchestrator.py     # Main coordinator
│   │   ├── housinggoal.py      # Housing goal agent
│   │   ├── BankData.py         # Bank data analyzer
│   │   ├── RiskProfiler.py     # Risk assessment
│   │   ├── PlanGenerator.py    # Plan generation
│   │   ├── WorkflowRouterAgent.py  # Workflow routing
│   │   ├── PropertyPriceAgent.py   # Property price search
│   │   └── schema.py           # Data models
│   │
│   ├── Prompts/                # Agent prompts
│   │   ├── OrchestratorPrompt.py
│   │   ├── HousingGoalPrompt.py
│   │   ├── BankDataPrompt.py
│   │   ├── RiskProfilerPrompt.py
│   │   └── PlanGeneratorPrompt.py
│   │
│   ├── tools/                  # Agent tools
│   │   ├── FileLoadTool.py     # File handling
│   │   ├── FinancialTools.py   # Financial calculations
│   │   ├── WebSearch.py        # Web search integration
│   │   ├── StatePersisterTool.py  # State management
│   │   └── utils.py            # Shared utilities
│   │
│   └── auth/                   # Authentication (if needed)
│       ├── auth.py
│       └── secret_manager.py
│
├── data/                       # Sample data files
│   └── bankstatement.csv       # Example bank statement
│
├── tests/                      # Test files
│   └── test_eval_agent.py
│
└── docs/                       # Documentation
    └── DEPLOYMENT.md           # Deployment guide
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

The system expects CSV bank statements with columns:
- `Date` - Transaction date
- `Description` - Transaction description
- `Amount` - Transaction amount (positive = credit, negative = debit)
- `Balance` - Account balance after transaction

Example: [data/bankstatement.csv](data/bankstatement.csv)

## Development

### Running Tests

```bash
pytest tests/
```

### Adding a New Agent

1. Create agent file in `src/agent/`
2. Define agent prompt in `src/Prompts/`
3. Register agent in orchestrator tools
4. Add to agent factory if needed

### Custom Tools

Create tools in `src/tools/` and register with agents:

```python
from google.adk.tools import Tool

@Tool
def my_custom_tool(param: str) -> dict:
    """Tool description for the LLM."""
    # Tool implementation
    return {"result": "..."}
```

## Security

- API keys stored in Google Cloud Secret Manager
- Environment variables for configuration
- Service account authentication for cloud resources
- No hardcoded credentials in code
- `.gitignore` configured for sensitive files

See [src/auth/README.md](src/auth/README.md) for authentication setup.

## Monitoring and Logging

- Structured logging to `housing_goal_agent.log`
- Cloud Trace integration (when deployed)
- Session state persistence
- Event logging for agent interactions

View logs:
```bash
# Local logs
tail -f housing_goal_agent.log

# Cloud logs (when deployed)
gcloud logging tail "resource.type=aiplatform_agent_engine"
```

## Troubleshooting

### Common Issues

**Import errors**: Ensure all dependencies installed
```bash
pip install -r requirements.txt
```

**API key issues**: Verify Secret Manager access
```bash
gcloud secrets describe SECRET_NAME --project=PROJECT_ID
```

**Session issues**: Clear session database
```bash
rm sessions.db
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
- Check [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for deployment help
- Review logs for error details
- Verify environment configuration in `.env`

## Acknowledgments

Built with:
- Google Agent Development Kit (ADK)
- Google Gemini AI
- Google Cloud Platform services
