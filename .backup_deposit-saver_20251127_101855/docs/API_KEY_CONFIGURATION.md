# API Key Configuration Guide

This guide explains how the Google API key is managed for Vertex AI Express Mode in the deposit-saver application.

## Overview

The application uses a Google API key stored in **Google Cloud Secret Manager** to enable Vertex AI Express Mode for improved performance and faster session initialization.

## Configuration

### Environment Variable

In your `.env` file:

```bash
# Google API Key for Vertex AI Express Mode (Secret Manager path)
GOOGLE_API_KEY_SECRET=projects/485422000664/secrets/DEMO-ACCOUNT_API-KEY
```

This environment variable specifies the **full path** to the secret in Google Cloud Secret Manager.

### Secret Manager Structure

- **Project ID**: `485422000664`
- **Secret Name**: `DEMO-ACCOUNT_API-KEY`
- **Version**: `latest` (automatically fetched at runtime)
- **Full Path**: `projects/485422000664/secrets/DEMO-ACCOUNT_API-KEY/versions/latest`

## How It Works

### 1. Runtime Retrieval

When the application starts, it retrieves the API key from Secret Manager:

```python
# Load from environment
GOOGLE_API_KEY_SECRET = os.getenv("GOOGLE_API_KEY_SECRET")

# Retrieve from Secret Manager
express_mode_api_key = get_api_key_from_secret(GOOGLE_API_KEY_SECRET)

# Use in VertexAiSessionService
session_service = VertexAiSessionService(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    express_mode_api_key=express_mode_api_key
)
```

### 2. Helper Function

The `get_api_key_from_secret()` function in [main.py](../main.py):

```python
def get_api_key_from_secret(secret_path: str) -> str:
    """
    Retrieve API key from Google Cloud Secret Manager.

    Args:
        secret_path: Full secret path (e.g., 'projects/PROJECT_ID/secrets/SECRET_NAME')

    Returns:
        API key string
    """
    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()

    # Add /versions/latest if not already in path
    if "/versions/" not in secret_path:
        secret_path = f"{secret_path}/versions/latest"

    try:
        response = client.access_secret_version(name=secret_path)
        api_key = response.payload.data.decode('UTF-8')
        logger.info(f"Successfully retrieved API key from secret")
        return api_key
    except Exception as e:
        logger.error(f"Failed to retrieve API key from {secret_path}: {e}")
        raise
```

## Security Benefits

### 1. No Hardcoded Credentials
✅ API key is **never** stored in source code
✅ Not committed to version control
✅ Not visible in application logs (only masked references)

### 2. Centralized Management
✅ Single source of truth in Secret Manager
✅ Easy rotation without code changes
✅ Audit trail of all access

### 3. Access Control
✅ Fine-grained IAM permissions
✅ Only authorized services/users can access
✅ Automatic credential management

## Permissions Required

### For Local Development

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Verify access to the secret
gcloud secrets versions access latest \
  --secret=DEMO-ACCOUNT_API-KEY \
  --project=485422000664
```

### For Production (Service Account)

The service account needs the **Secret Manager Secret Accessor** role:

```bash
# Grant permission to service account
gcloud secrets add-iam-policy-binding DEMO-ACCOUNT_API-KEY \
  --project=485422000664 \
  --member="serviceAccount:YOUR-SA@capstone-project-479414.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

Or at project level:

```bash
gcloud projects add-iam-policy-binding 485422000664 \
  --member="serviceAccount:YOUR-SA@capstone-project-479414.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Managing the API Key

### View Current Key

```bash
# View secret metadata
gcloud secrets describe DEMO-ACCOUNT_API-KEY --project=485422000664

# Access the key value (use with caution)
gcloud secrets versions access latest \
  --secret=DEMO-ACCOUNT_API-KEY \
  --project=485422000664
```

### Update the Key

To rotate or update the API key:

```bash
# Create new version with new API key value
echo -n "new-api-key-value" | gcloud secrets versions add DEMO-ACCOUNT_API-KEY \
  --project=485422000664 \
  --data-file=-
```

The application will automatically use the new key on next restart (since it fetches `latest` version).

### Create the Secret (First Time Setup)

If the secret doesn't exist:

```bash
# Create the secret
gcloud secrets create DEMO-ACCOUNT_API-KEY \
  --project=485422000664 \
  --replication-policy="automatic"

# Add the API key value
echo -n "your-api-key-value" | gcloud secrets versions add DEMO-ACCOUNT_API-KEY \
  --project=485422000664 \
  --data-file=-
```

## Vertex AI Express Mode

### What is Express Mode?

Express Mode is a Vertex AI feature that provides:
- **Faster session initialization** (~50% reduction in startup time)
- **Reduced latency** for agent operations
- **Better performance** for production workloads
- **Enhanced reliability** with optimized resource allocation

### Benefits

| Feature | Standard Mode | Express Mode |
|---------|--------------|--------------|
| Session Init | ~2-3 seconds | ~1 second |
| API Latency | Higher | Lower |
| Resource Allocation | Standard | Optimized |
| Cost | Standard | Slightly higher |

## Troubleshooting

### Error: "Failed to retrieve API key from Secret Manager"

**Cause**: Missing permissions or incorrect secret path

**Solution**:
1. Verify the secret path in `.env` matches the actual secret
2. Check authentication: `gcloud auth application-default print-access-token`
3. Verify permissions: `gcloud secrets get-iam-policy DEMO-ACCOUNT_API-KEY --project=485422000664`

### Error: "Secret not found"

**Cause**: Secret doesn't exist or wrong project

**Solution**:
```bash
# List all secrets in project
gcloud secrets list --project=485422000664

# Check if specific secret exists
gcloud secrets describe DEMO-ACCOUNT_API-KEY --project=485422000664
```

### Error: "Invalid API key"

**Cause**: The API key value is invalid or expired

**Solution**:
1. Verify the key works with Vertex AI
2. Check key hasn't been revoked
3. Generate a new key and update the secret
4. Contact GCP administrator

### Application doesn't start

**Cause**: API key retrieval fails during initialization

**Solution**:
1. Check logs: `cat housing_goal_agent.log`
2. Look for error message from `get_api_key_from_secret()`
3. Verify all permissions are in place
4. Test secret access manually (see above)

## Best Practices

### 1. Use Latest Version
✅ Always fetch `latest` version for automatic updates
✅ Allows key rotation without code changes

### 2. Implement Error Handling
```python
try:
    api_key = get_api_key_from_secret(GOOGLE_API_KEY_SECRET)
except Exception as e:
    logger.error(f"Failed to get API key: {e}")
    # Implement fallback or graceful degradation
```

### 3. Monitor Access
- Enable audit logging in Secret Manager
- Set up alerts for failed access attempts
- Regularly review access patterns

### 4. Rotate Regularly
- Update API key every 90 days
- Use versioning in Secret Manager
- Test new key before disabling old one

### 5. Limit Access
- Grant minimum required permissions
- Use service-specific service accounts
- Avoid using personal credentials in production

## Integration with Other Services

The same Secret Manager pattern is used for:
- **Firebase API Key**: `projects/485422000664/secrets/capstone-project-firebase-config`
- **Backend API Keys**: As needed
- **Database Credentials**: If applicable

This provides consistent, secure credential management across the application.

## Resources

- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Vertex AI Express Mode](https://cloud.google.com/vertex-ai/docs/express-mode)
- [IAM Best Practices](https://cloud.google.com/iam/docs/best-practices)
- [Session Service Documentation](SESSION_SERVICE.md)

## Support

For issues with API key configuration:
1. Check application logs: `housing_goal_agent.log`
2. Verify Secret Manager permissions
3. Review `.env` configuration
4. Test secret access with gcloud CLI
5. Contact your GCP administrator if needed
