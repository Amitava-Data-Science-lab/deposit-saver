# Deployment Guide - Vertex AI Agent Engines

This guide explains how to deploy the mortgage deposit agent to Vertex AI Agent Engines using `deploy_remote.py`.

## Overview

The deployment script creates a remote agent engine on Google Cloud Platform that:
- Runs your agent in a managed, scalable environment
- Automatically handles dependencies and environment setup
- Provides built-in monitoring and tracing
- Scales from 0 to 10 instances based on load

## Prerequisites

1. **Google Cloud Project Setup**
   ```bash
   gcloud auth application-default login
   gcloud config set project capstone-project-479414
   ```

2. **Enable Required APIs**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   ```

3. **Environment Variables**
   Ensure your `.env` file contains all required configuration (see `.env.example`)

## Environment Variables

The deployment script automatically passes these environment variables to the deployed agent:

### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | `capstone-project-479414` |
| `GOOGLE_CLOUD_LOCATION` | GCP region | `us-central1` |
| `GOOGLE_GENAI_USE_VERTEXAI` | Enable Vertex AI | `True` |
| `GOOGLE_CLOUD_STAGING_BUCKET` | Staging bucket for deployment | `gs://capstone-project-479414-staging` |

### Firebase Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `FIREBASE_SECRET_PROJECT_ID` | Project ID for Firebase secrets | `485422000664` |
| `FIREBASE_SECRET_NAME` | Secret name for Firebase config | `capstone-project-firebase-config` |
| `FIREBASE_SECRET_VERSION` | Secret version | `latest` |

### API Keys

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY_SECRET` | Secret Manager path for API key | `projects/485422000664/secrets/DEMO-ACCOUNT_API-KEY` |

## Deployment Process

### 1. Configure Environment

Create or update your `.env` file:

```bash
# GCP Configuration
GOOGLE_CLOUD_PROJECT=capstone-project-479414
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_CLOUD_STAGING_BUCKET=gs://capstone-project-479414-staging

# Firebase Configuration
FIREBASE_SECRET_PROJECT_ID=485422000664
FIREBASE_SECRET_NAME=capstone-project-firebase-config
FIREBASE_SECRET_VERSION=latest

# Google API Key for Vertex AI Express Mode
GOOGLE_API_KEY_SECRET=projects/485422000664/secrets/DEMO-ACCOUNT_API-KEY
```

### 2. Run Deployment

```bash
python deploy_remote.py
```

### 3. Monitor Deployment

The script will:
1. Load environment variables from `.env`
2. Display configuration being used
3. Create the agent engine with all dependencies
4. Upload your code packages (`src`, `mortgage_deposit_agent`)
5. Configure autoscaling (0-10 instances)
6. Return the deployed agent's resource name

**Expected Output:**
```
Project:, capstone-project-479414
Location:, us-central1
Staging Bucket:, gs://capstone-project-479414-staging
Use Vertex AI:, True

Environment variables to be set in deployed agent:
  GOOGLE_CLOUD_PROJECT: capstone-project-479414
  GOOGLE_CLOUD_LOCATION: us-central1
  GOOGLE_GENAI_USE_VERTEXAI: True
  GOOGLE_CLOUD_STAGING_BUCKET: gs://capstone-project-479414-staging
  FIREBASE_SECRET_PROJECT_ID: 485422000664
  FIREBASE_SECRET_NAME: capstone-project-firebase-config
  FIREBASE_SECRET_VERSION: latest
  GOOGLE_API_KEY_SECRET: projects/485422000664/secrets/...

Deployment finished!
Resource Name: projects/capstone-project-479414/locations/us-central1/agentEngines/mortgage_deposit_agent_xxxxx
```

## How It Works

### Environment Variable Injection

The deployment script prepares environment variables:

```python
# Load from .env file
load_dotenv()

# Prepare environment variables for deployed agent
env_vars = {
    "GOOGLE_CLOUD_PROJECT": os.environ["GOOGLE_CLOUD_PROJECT"],
    "GOOGLE_CLOUD_LOCATION": os.environ["GOOGLE_CLOUD_LOCATION"],
    # ... other variables
}

# Pass to agent_engines.create
remote_app = agent_engines.create(
    agent_engine=agent_app,
    env_vars=env_vars,  # Environment variables available in deployed agent
    # ... other configuration
)
```

### Dependency Management

All required Python packages are automatically installed:

```python
requirements=[
    "google-cloud-aiplatform[adk,agent_engines]",
    "google-genai",
    "pandas",
    "google-cloud-storage",
    "google-cloud-secret-manager",  # For accessing secrets
    "requests",
    "python-dotenv",
    # ... and more
]
```

### Code Packaging

Your application code is packaged and deployed:

```python
extra_packages=["src", "mortgage_deposit_agent"]
```

This includes:
- `src/` - All source code (agents, tools, auth modules)
- `mortgage_deposit_agent/` - Main agent implementation

### Resource Configuration

Autoscaling and resource limits:

```python
min_instances=0,        # Scale to zero when idle
max_instances=10,       # Scale up to 10 instances
resource_limits={
    "cpu": "2",         # 2 CPU cores per instance
    "memory": "2Gi"     # 2 GB RAM per instance
}
```

## Post-Deployment

### Verify Deployment

Check the deployed agent in GCP Console:
1. Navigate to **Vertex AI** > **Agent Engines**
2. Find `mortgage_deposit_agent`
3. Verify status is **ACTIVE**

### Test the Agent

```python
from vertexai import agent_engines

# Get reference to deployed agent
remote_app = agent_engines.get("mortgage_deposit_agent")

# Invoke the agent
response = remote_app.invoke(
    user_id="test_user",
    session_id="test_session",
    message="Help me plan for a 2-bed house in HP12"
)

print(response)
```

### View Logs

```bash
# View deployment logs
gcloud logging read "resource.type=aiplatform_agent_engine AND resource.labels.agent_engine_id=mortgage_deposit_agent" --limit 50

# Follow logs in real-time
gcloud logging tail "resource.type=aiplatform_agent_engine AND resource.labels.agent_engine_id=mortgage_deposit_agent"
```

### Monitor Performance

Use Cloud Console to monitor:
- **Request latency**
- **Instance count** (autoscaling)
- **Error rates**
- **Memory/CPU usage**

## Updating the Deployment

### Update Configuration

1. Modify `.env` file with new values
2. Re-run deployment:
   ```bash
   python deploy_remote.py
   ```

The script will update the existing agent engine with new configuration.

### Update Code

1. Make code changes in `src/` or `mortgage_deposit_agent/`
2. Re-run deployment:
   ```bash
   python deploy_remote.py
   ```

Code packages are automatically re-uploaded.

### Update Dependencies

1. Modify `requirements` list in `deploy_remote.py`
2. Re-run deployment

## Troubleshooting

### Error: "Permission denied"

**Solution**: Ensure you have the required IAM roles:

```bash
gcloud projects add-iam-policy-binding capstone-project-479414 \
  --member="user:your-email@example.com" \
  --role="roles/aiplatform.admin"
```

### Error: "Staging bucket not found"

**Solution**: Create the staging bucket:

```bash
gcloud storage buckets create gs://capstone-project-479414-staging \
  --project=capstone-project-479414 \
  --location=us-central1
```

### Error: "Secret not found"

**Solution**: Verify secrets exist:

```bash
# Check Firebase secret
gcloud secrets describe capstone-project-firebase-config --project=485422000664

# Check API key secret
gcloud secrets describe DEMO-ACCOUNT_API-KEY --project=485422000664
```

### Error: "Import error" in deployed agent

**Solution**:
1. Verify all required packages are in `requirements` list
2. Check that `extra_packages` includes all needed code directories
3. Review deployment logs for specific import errors

### Agent not responding

**Solution**:
1. Check agent status in Cloud Console
2. Verify environment variables are set correctly
3. Review logs for errors:
   ```bash
   gcloud logging read "resource.type=aiplatform_agent_engine" --limit 100
   ```

## Security Best Practices

### 1. Use Secret Manager
✅ All sensitive values (API keys, credentials) stored in Secret Manager
✅ Environment variables only contain **references** to secrets
✅ Secrets are retrieved at runtime by deployed agent

### 2. IAM Permissions
Ensure deployed agent's service account has:
- `roles/secretmanager.secretAccessor` - To read secrets
- `roles/aiplatform.user` - To use Vertex AI services
- `roles/storage.objectViewer` - To read from buckets

### 3. Network Security
- Deployed agents run in Google-managed VPC
- Outbound internet access for API calls
- Inbound access via authenticated API endpoints only

## Cost Optimization

### Minimize Costs
1. **Set min_instances=0**: Scale to zero when idle
2. **Right-size resources**: Use 2 CPU / 2Gi RAM (adjust if needed)
3. **Monitor usage**: Review Cloud Billing reports
4. **Delete unused deployments**: Clean up test deployments

### Estimate Costs
- **Compute**: Based on instance hours (CPU + memory)
- **Storage**: Staging bucket storage
- **Vertex AI**: API calls and session storage
- **Secret Manager**: Secret access operations

See [Vertex AI Pricing](https://cloud.google.com/vertex-ai/pricing) for current rates.

## Advanced Configuration

### Custom Service Account

Use a specific service account for the deployed agent:

```python
remote_app = agent_engines.create(
    agent_engine=agent_app,
    service_account="custom-sa@capstone-project-479414.iam.gserviceaccount.com",
    # ... other config
)
```

### VPC Configuration

Deploy into a specific VPC network:

```python
remote_app = agent_engines.create(
    agent_engine=agent_app,
    network="projects/capstone-project-479414/global/networks/my-vpc",
    # ... other config
)
```

### Custom Timeout

Set request timeout:

```python
remote_app = agent_engines.create(
    agent_engine=agent_app,
    timeout=300,  # 5 minutes
    # ... other config
)
```

## Resources

- [Vertex AI Agent Engines Documentation](https://cloud.google.com/vertex-ai/docs/agent-engines)
- [Environment Variables Guide](../README.md)
- [Session Service Configuration](SESSION_SERVICE.md)
- [API Key Configuration](API_KEY_CONFIGURATION.md)

## Support

For deployment issues:
1. Check deployment logs
2. Verify `.env` configuration
3. Ensure all secrets exist in Secret Manager
4. Review IAM permissions
5. Contact your GCP administrator if needed
