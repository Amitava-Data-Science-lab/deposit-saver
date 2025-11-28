# Firebase Authentication Module

This module provides comprehensive Firebase authentication functionality with Google Cloud Secret Manager integration for secure credential management.

## Features

- **Firebase Email/Password Authentication**: Authenticate users using Firebase Auth REST API
- **Token Management**: Automatic token refresh and expiration checking
- **JWT Token Exchange**: Exchange Firebase ID tokens for custom JWT tokens from your backend
- **Secret Manager Integration**: Automatically retrieve Firebase API key from Google Cloud Secret Manager
- **Multiple Configuration Options**: Support for Secret Manager, environment variables, or direct configuration

## Quick Start

### Installation

Add the required dependencies (already in requirements.txt):

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from src.auth import FirebaseAuth

# Initialize (automatically retrieves API key from Secret Manager)
auth = FirebaseAuth()

# Authenticate user
result = auth.get_firebase_token(
    email="user@example.com",
    password="password123"
)

print(f"User ID: {result['user_id']}")
print(f"Firebase Token: {result['id_token']}")
```

### Complete Authentication Flow (Firebase + JWT)

```python
from src.auth import authenticate

# One-liner for complete authentication
result = authenticate(
    email="user@example.com",
    password="password123"
)

# Access both tokens
firebase_token = result['firebase_id_token']
jwt_token = result['jwt_token']
user_id = result['user_id']
```

## Configuration

The module supports configuration through a `.env` file and multiple override options.

### Setup .env File

1. Copy the example file:
```bash
cp .env.example .env
```

2. The `.env` file contains the following Firebase configuration:
```bash
# Firebase Configuration
FIREBASE_SECRET_PROJECT_ID=485422000664
FIREBASE_SECRET_NAME=capstone-project-firebase-config
FIREBASE_SECRET_VERSION=latest

# Backend Configuration
BACKEND_URL=

# Optional: Override with direct Firebase API key (not recommended for production)
# FIREBASE_API_KEY=
```

### Configuration Methods (in order of precedence)

#### 1. Google Cloud Secret Manager (Recommended)

The Firebase API key is automatically retrieved from Secret Manager using configuration from `.env`:
- **Project ID**: `FIREBASE_SECRET_PROJECT_ID` (default: `485422000664`)
- **Secret Name**: `FIREBASE_SECRET_NAME` (default: `capstone-project-firebase-config`)
- **Secret Version**: `FIREBASE_SECRET_VERSION` (default: `latest`)

The secret should contain a JSON configuration with an `apiKey` field:
```json
{
  "apiKey": "your-firebase-api-key",
  "authDomain": "your-project.firebaseapp.com",
  "projectId": "your-project-id",
  ...
}
```

**Usage:**
```python
# Automatic - reads from .env file
auth = FirebaseAuth()

# Or disable if needed
auth = FirebaseAuth(use_secret_manager=False)
```

#### 2. Environment Variables (.env file)

Set the `FIREBASE_API_KEY` directly in your `.env` file (not recommended for production):
```bash
FIREBASE_API_KEY=your-firebase-api-key
BACKEND_URL=https://your-backend.com
```

#### 3. Direct Parameters

Override any configuration by passing parameters directly:
```python
auth = FirebaseAuth(
    api_key="your-firebase-api-key",
    backend_url="https://your-backend.com",
    use_secret_manager=False
)
```

## API Reference

### FirebaseAuth Class

#### Constructor

```python
FirebaseAuth(
    api_key: Optional[str] = None,
    backend_url: Optional[str] = None,
    use_secret_manager: bool = True,
    project_id: Optional[str] = None
)
```

**Parameters:**
- `api_key`: Firebase Web API key (optional if using Secret Manager)
- `backend_url`: Backend URL for JWT exchange (optional)
- `use_secret_manager`: Enable Secret Manager integration (default: True)
- `project_id`: GCP project ID (default: 485422000664)

#### Methods

##### `get_firebase_token(email, password)`

Authenticate with Firebase and get ID token.

```python
result = auth.get_firebase_token(
    email="user@example.com",
    password="password123"
)
```

**Returns:**
```python
{
    "id_token": "eyJhbG...",
    "refresh_token": "AMf-vBy...",
    "expires_in": "3600",
    "user_id": "abc123..."
}
```

##### `exchange_for_jwt(firebase_token=None, jwt_exchange_endpoint=None)`

Exchange Firebase token for custom JWT.

```python
jwt_result = auth.exchange_for_jwt()
```

**Returns:**
```python
{
    "jwt_token": "eyJhbG...",
    "expires_in": "3600",
    "token_type": "Bearer"
}
```

##### `authenticate_and_get_jwt(email, password, jwt_exchange_endpoint=None)`

Complete authentication flow in one call.

```python
result = auth.authenticate_and_get_jwt(
    email="user@example.com",
    password="password123"
)
```

**Returns:**
```python
{
    "firebase_id_token": "eyJhbG...",
    "firebase_refresh_token": "AMf-vBy...",
    "jwt_token": "eyJhbG...",
    "user_id": "abc123...",
    "firebase_expires_in": "3600",
    "jwt_token_type": "Bearer"
}
```

##### `refresh_id_token()`

Refresh an expired Firebase token.

```python
refreshed = auth.refresh_id_token()
```

##### `is_token_expired()`

Check if token needs refreshing.

```python
if auth.is_token_expired():
    auth.refresh_id_token()
```

##### `get_auth_header(use_jwt=True)`

Get authorization header for API requests.

```python
# Get JWT header
headers = auth.get_auth_header(use_jwt=True)
# Returns: {"Authorization": "Bearer eyJhbG..."}

# Get Firebase ID token header
headers = auth.get_auth_header(use_jwt=False)
```

### Convenience Functions

#### `authenticate()`

Quick authentication with all defaults.

```python
from src.auth import authenticate

result = authenticate(
    email="user@example.com",
    password="password123"
)
```

### Secret Manager Functions

#### `get_firebase_api_key()`

Retrieve just the API key from Secret Manager.

```python
from src.auth import get_firebase_api_key

api_key = get_firebase_api_key()
```

#### `get_firebase_config_from_secret()`

Retrieve complete Firebase configuration.

```python
from src.auth import get_firebase_config_from_secret

config = get_firebase_config_from_secret()
print(config['projectId'])
print(config['authDomain'])
```

## Usage Examples

### Example 1: Basic Authentication

```python
from src.auth import FirebaseAuth

auth = FirebaseAuth()

try:
    result = auth.get_firebase_token(
        email="user@example.com",
        password="password123"
    )
    print(f"Successfully authenticated: {result['user_id']}")
except ValueError as e:
    print(f"Authentication failed: {e}")
```

### Example 2: Complete Flow with JWT

```python
from src.auth import FirebaseAuth

auth = FirebaseAuth()

result = auth.authenticate_and_get_jwt(
    email="user@example.com",
    password="password123"
)

# Use JWT for API calls
jwt_token = result['jwt_token']
```

### Example 3: Making Authenticated API Calls

```python
import requests
from src.auth import FirebaseAuth

auth = FirebaseAuth()
auth.authenticate_and_get_jwt(
    email="user@example.com",
    password="password123"
)

# Get authorization header
headers = auth.get_auth_header(use_jwt=True)

# Make authenticated request
response = requests.get(
    "https://your-backend.com/api/user/profile",
    headers=headers
)

print(response.json())
```

### Example 4: Token Refresh

```python
from src.auth import FirebaseAuth

auth = FirebaseAuth()
auth.get_firebase_token("user@example.com", "password123")

# Later, check if token expired
if auth.is_token_expired():
    print("Token expired, refreshing...")
    auth.refresh_id_token()
    print("Token refreshed!")
```

### Example 5: Custom Backend Endpoint

```python
from src.auth import FirebaseAuth

auth = FirebaseAuth(backend_url="https://custom-backend.com")

result = auth.authenticate_and_get_jwt(
    email="user@example.com",
    password="password123",
    jwt_exchange_endpoint="https://custom-backend.com/api/v2/auth/token"
)
```

### Example 6: Using Secret Manager Directly

```python
from src.auth import get_firebase_config_from_secret, FirebaseAuth

# Get complete config
config = get_firebase_config_from_secret()

# Use specific fields
auth = FirebaseAuth(api_key=config['apiKey'])
```

## Architecture

### Authentication Flow

```
User Credentials (email/password)
    ↓
Firebase REST API
    ↓
Firebase ID Token + Refresh Token
    ↓
Backend API (JWT Exchange Endpoint)
    ↓
Custom JWT Token
```

### Secret Manager Integration

```
FirebaseAuth.__init__()
    ↓
Check if api_key provided? → No
    ↓
use_secret_manager=True?
    ↓
SecretManagerClient.get_firebase_config()
    ↓
Parse JSON → Extract apiKey
    ↓
Use for authentication
```

## Error Handling

The module provides detailed error messages:

```python
try:
    auth = FirebaseAuth()
    result = auth.get_firebase_token("user@example.com", "wrong_password")
except ValueError as e:
    # Handles:
    # - Invalid credentials
    # - Missing API key
    # - Network errors
    # - Invalid JSON responses
    print(f"Error: {e}")
```

## Security Best Practices

1. **Use Secret Manager**: Store API keys in Google Cloud Secret Manager, not in code or environment variables
2. **Token Refresh**: Always check token expiration before making API calls
3. **HTTPS Only**: All API calls use HTTPS
4. **No Token Logging**: Tokens are never logged in their entirety (only truncated for debugging)
5. **Minimal Permissions**: Request only necessary Firebase permissions

## Testing

See [example_usage.py](example_usage.py) for comprehensive examples of all features.

```python
# Run examples
python src/auth/example_usage.py
```

## Troubleshooting

### Issue: "Firebase API key must be provided"

**Solution**:
1. Ensure your `.env` file exists and contains the Firebase configuration
2. Verify the Secret Manager secret path is correct in `.env`:
   ```bash
   FIREBASE_SECRET_PROJECT_ID=485422000664
   FIREBASE_SECRET_NAME=capstone-project-firebase-config
   FIREBASE_SECRET_VERSION=latest
   ```
3. Or set `FIREBASE_API_KEY` directly in `.env` as a fallback

### Issue: "Failed to retrieve API key from Secret Manager"

**Solution**:
1. Verify you have the required GCP permissions
2. Check that the `.env` file exists in the project root
3. Verify the secret exists: `projects/485422000664/secrets/capstone-project-firebase-config`
4. Ensure your GCP credentials are configured: `gcloud auth application-default login`
5. Check that the secret name and project ID in `.env` match your actual GCP resources

### Issue: "JWT exchange failed"

**Solution**:
1. Set the `BACKEND_URL` in your `.env` file
2. Verify your backend endpoint accepts Firebase ID tokens
3. Check backend logs for detailed error messages

### Issue: ".env file not loaded"

**Solution**:
1. Ensure `.env` file is in the project root directory
2. Verify `python-dotenv` is installed: `pip install python-dotenv`
3. Check file permissions - `.env` should be readable

## Dependencies

- `google-cloud-secret-manager`: Google Cloud Secret Manager client
- `requests`: HTTP library for API calls
- `python-dotenv`: Load environment variables from .env file
- Python 3.7+

## License

Part of the deposit-saver application.
