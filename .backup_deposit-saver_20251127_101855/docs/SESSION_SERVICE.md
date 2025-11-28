# Session Service Configuration

This document explains the session service implementation in the deposit-saver application.

## Overview

The application has been configured to use **Vertex AI Session Service** for managing agent conversation sessions, replacing the previous SQLite-based session storage.

## Why Vertex AI Session Service?

### Benefits

1. **Cloud-Native**: Fully managed by Google Cloud Platform
2. **Scalable**: Automatically scales with your application needs
3. **Reliable**: Built-in redundancy and durability
4. **Integrated**: Seamlessly works with other Vertex AI services
5. **No Database Management**: No need to manage SQLite files or database migrations
6. **Multi-Region Support**: Can be deployed across different GCP regions

### Comparison with SQLite

| Feature | SQLite | Vertex AI Session Service |
|---------|--------|---------------------------|
| Deployment | Local file | Cloud-managed |
| Scalability | Limited (single file) | Highly scalable |
| Durability | Depends on disk | Built-in redundancy |
| Multi-instance | Challenging | Fully supported |
| Maintenance | Manual | Managed by GCP |
| Cost | Free (local) | Pay-as-you-go |

## Configuration

### Environment Variables

The session service is configured through `.env` file:

```bash
# GCP Configuration
GOOGLE_CLOUD_PROJECT=capstone-project-479414
GOOGLE_CLOUD_LOCATION=us-central1

# API Key for Vertex AI Express Mode (stored in Secret Manager)
GOOGLE_API_KEY_SECRET=projects/485422000664/secrets/DEMO-ACCOUNT_API-KEY
```

### Code Implementation

In [main.py](../main.py):

```python
from google.adk.sessions import VertexAiSessionService
from google.cloud import secretmanager

# Helper function to retrieve API key from Secret Manager
def get_api_key_from_secret(secret_path: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    if "/versions/" not in secret_path:
        secret_path = f"{secret_path}/versions/latest"
    response = client.access_secret_version(name=secret_path)
    return response.payload.data.decode('UTF-8')

# Retrieve API key from Secret Manager
GOOGLE_API_KEY_SECRET = os.getenv("GOOGLE_API_KEY_SECRET")
express_mode_api_key = get_api_key_from_secret(GOOGLE_API_KEY_SECRET)

# Initialize Vertex AI Session Service
session_service = VertexAiSessionService(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    express_mode_api_key=express_mode_api_key
)
```

### Express Mode API Key

The `express_mode_api_key` parameter enables Vertex AI Express Mode, which provides:
- Faster session initialization
- Reduced latency for agent operations
- Enhanced performance for production workloads

The API key is securely stored in Google Cloud Secret Manager at:
- **Secret Path**: `projects/485422000664/secrets/DEMO-ACCOUNT_API-KEY`
- **Version**: `latest` (automatically fetched)

**Security Note**: The API key is never hardcoded in the application. It's retrieved at runtime from Secret Manager, ensuring secure credential management.

### FastAPI Integration

The session service URI for FastAPI:

```python
SESSION_SERVICE_URI = f"vertexai://{GOOGLE_CLOUD_PROJECT}/{GOOGLE_CLOUD_LOCATION}"
```

## Session Management

### Creating a Session

```python
await session_service.create_session(
    app_name="housing_deposit_planner",
    user_id="user_123",
    session_id="session_456"
)
```

### Retrieving Session State

```python
current_session = await session_service.get_session(
    app_name="housing_deposit_planner",
    user_id="user_123",
    session_id="session_456"
)

# Access session state
state = current_session.state
```

### Using with Runners

```python
from google.adk.runners import Runner

runner = Runner(
    agent=orchestrator_agent,
    app_name="housing_deposit_planner",
    session_service=session_service  # Vertex AI Session Service
)
```

## Session Data Storage

### What Gets Stored

- **Conversation History**: All messages between user and agents
- **Agent State**: Output from each agent stored in session state
- **User Context**: User-specific data and preferences
- **Intermediate Results**: Tool outputs and processing results

### Data Location

Sessions are stored in Vertex AI within:
- **Project**: `capstone-project-479414`
- **Location**: `us-central1`

### Data Retention

Vertex AI Session Service manages data retention according to GCP policies. Sessions persist across application restarts and deployments.

## Migration from SQLite

### Before (SQLite)

```python
from google.adk.sessions import InMemorySessionService

SESSION_SERVICE_URI = "sqlite:///./sessions.db"
session_service = InMemorySessionService()
```

### After (Vertex AI)

```python
from google.adk.sessions import VertexAISessionService

SESSION_SERVICE_URI = f"vertexai://{GOOGLE_CLOUD_PROJECT}/{GOOGLE_CLOUD_LOCATION}"

session_service = VertexAISessionService(
    project_id=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION
)
```

### Data Migration

If you have existing SQLite session data:

1. **Export Sessions**: Extract session data from SQLite
2. **Transform Format**: Convert to Vertex AI format
3. **Import**: Use Vertex AI API to recreate sessions

Note: For new deployments, start fresh with Vertex AI Session Service.

## Permissions Required

### GCP IAM Roles

Ensure your service account or user has these permissions:

```bash
# Vertex AI User role
roles/aiplatform.user

# Or specific permissions
aiplatform.sessions.create
aiplatform.sessions.get
aiplatform.sessions.update
aiplatform.sessions.delete
aiplatform.sessions.list
```

### Grant Permissions

```bash
# Grant to service account
gcloud projects add-iam-policy-binding capstone-project-479414 \
  --member="serviceAccount:YOUR-SERVICE-ACCOUNT@capstone-project-479414.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Or grant to user
gcloud projects add-iam-policy-binding capstone-project-479414 \
  --member="user:your-email@example.com" \
  --role="roles/aiplatform.user"
```

## Local Development

For local development:

```bash
# Authenticate with your Google account
gcloud auth application-default login

# Set your project
gcloud config set project capstone-project-479414
```

The application will use your local credentials to access Vertex AI Session Service.

## Production Deployment

### Cloud Run / Cloud Functions

Use a service account with appropriate permissions:

```bash
# Create service account
gcloud iam service-accounts create mortgage-deposit-sa \
  --display-name="Mortgage Deposit Service Account"

# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding capstone-project-479414 \
  --member="serviceAccount:mortgage-deposit-sa@capstone-project-479414.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Deploy with service account
gcloud run deploy mortgage-deposit-service \
  --service-account=mortgage-deposit-sa@capstone-project-479414.iam.gserviceaccount.com
```

## Monitoring

### View Session Activity

Use Google Cloud Console:

1. Navigate to **Vertex AI** > **Sessions**
2. Filter by project: `capstone-project-479414`
3. View active and historical sessions

### Logging

Session operations are logged:

```python
logger.info(f"Initializing Vertex AI Session Service with project: {GOOGLE_CLOUD_PROJECT}")
logger.info(f"Starting orchestrator session. Session ID: {SESSION_ID}")
```

View logs in Cloud Logging:

```bash
gcloud logging read "resource.type=vertex_ai_session" --project=capstone-project-479414
```

## Troubleshooting

### Issue: "Permission denied accessing Vertex AI"

**Solution**:
```bash
# Verify authentication
gcloud auth application-default print-access-token

# Check project
gcloud config get-value project

# Verify permissions
gcloud projects get-iam-policy capstone-project-479414
```

### Issue: "Session not found"

**Solution**:
- Verify `app_name`, `user_id`, and `session_id` match when creating and retrieving
- Check that session was created before attempting to retrieve
- Ensure sessions haven't expired (check Vertex AI retention policies)

### Issue: "Wrong project or location"

**Solution**:
- Verify `.env` file has correct values:
  ```bash
  GOOGLE_CLOUD_PROJECT=capstone-project-479414
  GOOGLE_CLOUD_LOCATION=us-central1
  ```
- Ensure `.env` is in project root directory
- Restart application after changing `.env`

### Issue: "Failed to retrieve API key from Secret Manager"

**Solution**:
1. Verify the secret exists:
   ```bash
   gcloud secrets describe DEMO-ACCOUNT_API-KEY --project=485422000664
   ```

2. Check you have access permissions:
   ```bash
   gcloud secrets versions access latest \
     --secret=DEMO-ACCOUNT_API-KEY \
     --project=485422000664
   ```

3. Verify the secret path in `.env`:
   ```bash
   GOOGLE_API_KEY_SECRET=projects/485422000664/secrets/DEMO-ACCOUNT_API-KEY
   ```

4. Grant Secret Manager permissions if needed:
   ```bash
   gcloud projects add-iam-policy-binding 485422000664 \
     --member="user:your-email@example.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

### Issue: "Invalid API key for Vertex AI Express Mode"

**Solution**:
- Ensure the API key stored in Secret Manager is valid
- Verify the key hasn't expired
- Check the key has necessary Vertex AI permissions
- Contact your GCP administrator to regenerate the key if needed

## Cost Considerations

Vertex AI Session Service pricing:
- **Session Storage**: Charged per GB-month
- **API Calls**: Charged per operation
- **Data Transfer**: Standard GCP networking charges

For current pricing, see: [Vertex AI Pricing](https://cloud.google.com/vertex-ai/pricing)

## Best Practices

1. **Use Meaningful Session IDs**: Include user context in session ID for easier debugging
   ```python
   SESSION_ID = f"user_{user_id}_{timestamp}"
   ```

2. **Clean Up Old Sessions**: Implement session cleanup for inactive users
   ```python
   # Delete old sessions periodically
   await session_service.delete_session(app_name, user_id, session_id)
   ```

3. **Session State Management**: Store minimal data in session state
   - Keep state lightweight
   - Store large data in Cloud Storage and reference in session

4. **Error Handling**: Always handle session errors gracefully
   ```python
   try:
       session = await session_service.get_session(app_name, user_id, session_id)
   except Exception as e:
       logger.error(f"Failed to retrieve session: {e}")
       # Create new session or handle gracefully
   ```

## Resources

- [Google ADK Sessions Documentation](https://cloud.google.com/vertex-ai/docs/adk/sessions)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [GCP IAM Documentation](https://cloud.google.com/iam/docs)

## Support

For issues with session service:
1. Check application logs in `housing_goal_agent.log`
2. Verify GCP permissions and authentication
3. Review Vertex AI console for session status
4. Check `.env` configuration
