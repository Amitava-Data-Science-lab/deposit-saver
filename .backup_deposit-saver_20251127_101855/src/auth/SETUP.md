# Firebase Authentication Setup Guide

Quick start guide for setting up Firebase authentication with Google Cloud Secret Manager.

## Prerequisites

- Python 3.7+
- Google Cloud Project with Secret Manager enabled
- Firebase project configured
- GCP credentials configured locally

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `google-cloud-secret-manager`
- `requests`
- `python-dotenv`
- Other project dependencies

## Step 2: Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. The `.env` file is pre-configured with the correct values:
```bash
# Firebase Configuration
FIREBASE_SECRET_PROJECT_ID=485422000664
FIREBASE_SECRET_NAME=capstone-project-firebase-config
FIREBASE_SECRET_VERSION=latest

# Backend Configuration (set this if using JWT exchange)
BACKEND_URL=
```

**Note**: The `.env` file is already gitignored, so your configuration is safe.

## Step 3: Verify Secret Manager Access

Ensure the Firebase configuration secret exists in Google Cloud Secret Manager:

```bash
# Check if secret exists
gcloud secrets describe capstone-project-firebase-config \
  --project=485422000664

# View secret value (for verification only - don't share this!)
gcloud secrets versions access latest \
  --secret=capstone-project-firebase-config \
  --project=485422000664
```

The secret should contain a JSON configuration:
```json
{
  "apiKey": "your-firebase-api-key",
  "authDomain": "your-project.firebaseapp.com",
  "projectId": "your-project-id",
  "storageBucket": "your-project.appspot.com",
  "messagingSenderId": "123456789",
  "appId": "1:123456789:web:abcdef"
}
```

## Step 4: Authenticate with Google Cloud

Ensure your local environment is authenticated:

```bash
# Authenticate with your Google account
gcloud auth application-default login

# Verify authentication
gcloud auth application-default print-access-token
```

## Step 5: Test the Authentication

Run a simple test to verify everything works:

```python
from src.auth import FirebaseAuth

# Initialize (automatically reads from .env and retrieves API key from Secret Manager)
auth = FirebaseAuth()

# Authenticate a user
result = auth.get_firebase_token(
    email="test@example.com",
    password="test_password"
)

print(f"✓ Authentication successful!")
print(f"User ID: {result['user_id']}")
```

## Step 6: (Optional) Configure Backend URL

If you're using JWT token exchange, set the backend URL in `.env`:

```bash
BACKEND_URL=https://your-backend-api.com
```

Then test the complete flow:

```python
from src.auth import authenticate

result = authenticate(
    email="test@example.com",
    password="test_password"
)

print(f"Firebase Token: {result['firebase_id_token'][:30]}...")
print(f"JWT Token: {result['jwt_token'][:30]}...")
```

## Configuration Priority

The authentication module checks for configuration in this order:

1. **Direct parameters** passed to `FirebaseAuth()` constructor
2. **Google Cloud Secret Manager** (configured via `.env`)
3. **Environment variable** `FIREBASE_API_KEY` (from `.env` or system)

## Common Issues

### "Permission denied" when accessing Secret Manager

**Solution**:
```bash
# Grant yourself the Secret Manager Secret Accessor role
gcloud projects add-iam-policy-binding 485422000664 \
  --member="user:your-email@example.com" \
  --role="roles/secretmanager.secretAccessor"
```

### "Secret not found"

**Solution**: Verify the secret name and project ID in your `.env` file match the actual secret in GCP.

### ".env file not loaded"

**Solution**: Ensure the `.env` file is in the **project root directory** (same level as `requirements.txt`), not in the `src/auth/` directory.

## Security Best Practices

1. ✅ **DO** use Secret Manager for production
2. ✅ **DO** keep `.env` file in `.gitignore`
3. ✅ **DO** use different secrets for dev/staging/production
4. ❌ **DON'T** commit `.env` file to git
5. ❌ **DON'T** hardcode API keys in source code
6. ❌ **DON'T** share your `.env` file with others

## Next Steps

- Read the [complete documentation](README.md)
- Check out [usage examples](example_usage.py)
- See [integration patterns](integration_example.py)

## Quick Reference

### Basic Authentication
```python
from src.auth import FirebaseAuth

auth = FirebaseAuth()
result = auth.get_firebase_token("email@example.com", "password")
```

### Complete Flow (Firebase + JWT)
```python
from src.auth import authenticate

result = authenticate("email@example.com", "password")
jwt_token = result['jwt_token']
```

### Making Authenticated Requests
```python
import requests
from src.auth import FirebaseAuth

auth = FirebaseAuth()
auth.authenticate_and_get_jwt("email@example.com", "password")

headers = auth.get_auth_header(use_jwt=True)
response = requests.get("https://api.example.com/data", headers=headers)
```

## Support

For issues or questions:
1. Check the [README](README.md) for detailed documentation
2. Review [example_usage.py](example_usage.py) for working examples
3. Verify your `.env` configuration matches `.env.example`
