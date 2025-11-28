"""
Example usage of the Firebase Authentication module.

This demonstrates how to:
1. Get a Firebase ID token using email/password
2. Exchange the Firebase token for a custom JWT token
3. Use the complete authentication flow
"""

import asyncio
import logging
from auth import FirebaseAuth, authenticate

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_basic_firebase_auth():
    """Example: Get Firebase ID token only (using Secret Manager)"""
    print("\n=== Example 1: Basic Firebase Authentication (Secret Manager) ===\n")

    # Initialize the auth client
    # API key will be automatically retrieved from Google Cloud Secret Manager
    # Secret: projects/485422000664/secrets/capstone-project-firebase-config
    auth_client = FirebaseAuth()

    # Authenticate with email and password
    try:
        result = auth_client.get_firebase_token(
            email="user@example.com",
            password="your_password"
        )

        print(f"✓ Authentication successful!")
        print(f"  User ID: {result['user_id']}")
        print(f"  Token expires in: {result['expires_in']} seconds")
        print(f"  ID Token: {result['id_token'][:50]}...")

    except ValueError as e:
        print(f"✗ Authentication failed: {e}")


def example_token_refresh():
    """Example: Refresh an expired Firebase token"""
    print("\n=== Example 2: Token Refresh ===\n")

    auth_client = FirebaseAuth()

    # First authenticate
    try:
        auth_client.get_firebase_token(
            email="user@example.com",
            password="your_password"
        )

        print("✓ Initial authentication successful")

        # Check if token is expired
        if auth_client.is_token_expired():
            print("Token is expired, refreshing...")
            refresh_result = auth_client.refresh_id_token()
            print(f"✓ Token refreshed successfully")
            print(f"  New token expires in: {refresh_result['expires_in']} seconds")
        else:
            print("Token is still valid")

    except ValueError as e:
        print(f"✗ Error: {e}")


def example_jwt_exchange():
    """Example: Complete flow - Firebase auth + JWT exchange"""
    print("\n=== Example 3: Complete Authentication Flow ===\n")

    # Make sure both FIREBASE_API_KEY and BACKEND_URL are set
    auth_client = FirebaseAuth()

    try:
        # Complete authentication flow
        result = auth_client.authenticate_and_get_jwt(
            email="user@example.com",
            password="your_password"
        )

        print(f"✓ Complete authentication successful!")
        print(f"  User ID: {result['user_id']}")
        print(f"  Firebase Token: {result['firebase_id_token'][:50]}...")
        print(f"  JWT Token: {result['jwt_token'][:50]}...")
        print(f"  Token Type: {result['jwt_token_type']}")

        # Get authorization header for API calls
        auth_header = auth_client.get_auth_header(use_jwt=True)
        print(f"\n  Authorization Header: {auth_header}")

    except ValueError as e:
        print(f"✗ Authentication failed: {e}")


def example_convenience_function():
    """Example: Using the convenience function"""
    print("\n=== Example 4: Convenience Function ===\n")

    try:
        # Quick one-liner authentication
        result = authenticate(
            email="user@example.com",
            password="your_password"
        )

        print(f"✓ Authentication successful!")
        print(f"  User ID: {result['user_id']}")
        print(f"  JWT Token: {result['jwt_token'][:50]}...")

    except ValueError as e:
        print(f"✗ Authentication failed: {e}")


def example_custom_backend_endpoint():
    """Example: Using a custom JWT exchange endpoint"""
    print("\n=== Example 5: Custom Backend Endpoint ===\n")

    auth_client = FirebaseAuth(
        api_key="your_firebase_api_key",
        backend_url="https://your-backend.com"
    )

    try:
        # Authenticate and exchange with custom endpoint
        result = auth_client.authenticate_and_get_jwt(
            email="user@example.com",
            password="your_password",
            jwt_exchange_endpoint="https://your-backend.com/api/v1/auth/token-exchange"
        )

        print(f"✓ Authentication with custom endpoint successful!")
        print(f"  JWT Token: {result['jwt_token'][:50]}...")

    except ValueError as e:
        print(f"✗ Authentication failed: {e}")


def example_making_authenticated_requests():
    """Example: Making API calls with the JWT token"""
    print("\n=== Example 6: Making Authenticated API Requests ===\n")

    import requests

    auth_client = FirebaseAuth()

    try:
        # Authenticate
        result = auth_client.authenticate_and_get_jwt(
            email="user@example.com",
            password="your_password"
        )

        print("✓ Authentication successful")

        # Get authorization header
        headers = auth_client.get_auth_header(use_jwt=True)

        # Make an authenticated API call
        api_url = "https://your-backend.com/api/user/profile"
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            print(f"✓ API call successful")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ API call failed: {response.status_code}")

    except ValueError as e:
        print(f"✗ Error: {e}")
    except requests.RequestException as e:
        print(f"✗ Request error: {e}")


def example_secret_manager_integration():
    """Example: Using Secret Manager to retrieve Firebase config"""
    print("\n=== Example 7: Secret Manager Integration ===\n")

    from secret_manager import get_firebase_api_key, get_firebase_config_from_secret

    try:
        # Get just the API key
        api_key = get_firebase_api_key()
        print(f"✓ Retrieved Firebase API key from Secret Manager")
        print(f"  API Key: {api_key[:20]}...")

        # Get complete Firebase config
        config = get_firebase_config_from_secret()
        print(f"\n✓ Retrieved complete Firebase configuration")
        print(f"  Project ID: {config.get('projectId')}")
        print(f"  Auth Domain: {config.get('authDomain')}")

        # Use the API key for authentication
        auth_client = FirebaseAuth(api_key=api_key)
        print(f"\n✓ FirebaseAuth client initialized with Secret Manager API key")

    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Firebase Authentication Examples")
    print("="*60)

    print("\nConfiguration Options:")
    print("  1. (RECOMMENDED) Google Cloud Secret Manager:")
    print("     Secret: projects/485422000664/secrets/capstone-project-firebase-config")
    print("     The FirebaseAuth class automatically retrieves the API key from here")
    print("\n  2. Environment Variables (fallback):")
    print("     - FIREBASE_API_KEY: Your Firebase Web API key")
    print("     - BACKEND_URL: Your backend server URL (for JWT exchange)")
    print("\n  3. Direct parameters to FirebaseAuth constructor")

    # Run examples (comment out the ones you don't want to run)

    # example_basic_firebase_auth()
    # example_token_refresh()
    # example_jwt_exchange()
    # example_convenience_function()
    # example_custom_backend_endpoint()
    # example_making_authenticated_requests()
    # example_secret_manager_integration()

    print("\n" + "="*60)
    print("Examples completed")
    print("="*60 + "\n")
