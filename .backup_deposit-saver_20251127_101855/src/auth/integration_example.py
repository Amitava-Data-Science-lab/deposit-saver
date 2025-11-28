"""
Integration example showing how to use Firebase authentication in the deposit-saver application.

This demonstrates a realistic authentication flow that could be used in main.py
or in API endpoints.
"""

import logging
import asyncio
from typing import Optional, Dict
from src.auth import FirebaseAuth, authenticate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthenticatedSession:
    """
    Manages an authenticated user session with automatic token refresh.
    """

    def __init__(self, email: str, password: str, backend_url: Optional[str] = None):
        """
        Initialize authenticated session.

        Args:
            email: User email
            password: User password
            backend_url: Optional backend URL for JWT exchange
        """
        self.email = email
        self.password = password
        self.auth = FirebaseAuth(backend_url=backend_url)
        self.is_authenticated = False

    def login(self) -> Dict[str, str]:
        """
        Authenticate user and get tokens.

        Returns:
            Dict with authentication result
        """
        logger.info(f"Logging in user: {self.email}")

        try:
            result = self.auth.authenticate_and_get_jwt(
                email=self.email,
                password=self.password
            )

            self.is_authenticated = True
            logger.info(f"✓ Successfully authenticated user: {result['user_id']}")

            return result

        except ValueError as e:
            logger.error(f"✗ Authentication failed: {e}")
            self.is_authenticated = False
            raise

    def get_auth_headers(self, use_jwt: bool = True) -> Dict[str, str]:
        """
        Get authorization headers for API requests.
        Automatically refreshes token if expired.

        Args:
            use_jwt: If True, returns JWT token. If False, returns Firebase ID token

        Returns:
            Dict with Authorization header
        """
        if not self.is_authenticated:
            raise ValueError("User not authenticated. Call login() first.")

        # Check if token expired and refresh if needed
        if self.auth.is_token_expired():
            logger.info("Token expired, refreshing...")
            self.auth.refresh_id_token()
            logger.info("Token refreshed successfully")

        return self.auth.get_auth_header(use_jwt=use_jwt)

    def make_authenticated_request(self, url: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """
        Make an authenticated HTTP request.

        Args:
            url: API endpoint URL
            method: HTTP method (GET, POST, etc.)
            data: Optional request data

        Returns:
            Response data as dict
        """
        import requests

        headers = self.get_auth_headers(use_jwt=True)

        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()


async def example_integration_with_main():
    """
    Example showing how to integrate authentication with the main application flow.
    """
    logger.info("\n=== Integration Example with Main Application ===\n")

    # Step 1: Authenticate user
    session = AuthenticatedSession(
        email="user@example.com",
        password="password123",
        backend_url="https://your-backend.com"
    )

    try:
        # Login
        auth_result = session.login()
        user_id = auth_result['user_id']

        logger.info(f"User {user_id} authenticated successfully")

        # Step 2: Use authentication in your application
        # For example, making authenticated API calls for housing goals

        # Get user profile
        try:
            headers = session.get_auth_headers(use_jwt=True)
            logger.info(f"Authorization header ready: {list(headers.keys())}")

            # Example: Make authenticated request to get user data
            # user_data = session.make_authenticated_request(
            #     url="https://your-backend.com/api/user/profile",
            #     method="GET"
            # )

            # Example: Submit housing goal with authentication
            # housing_goal_response = session.make_authenticated_request(
            #     url="https://your-backend.com/api/housing-goals",
            #     method="POST",
            #     data={"location": "HP12", "bedrooms": 2}
            # )

        except Exception as e:
            logger.error(f"Error making authenticated request: {e}")

    except ValueError as e:
        logger.error(f"Authentication failed: {e}")


def example_simple_auth_flow():
    """
    Simplest possible authentication flow.
    """
    logger.info("\n=== Simple Authentication Flow ===\n")

    try:
        # One-line authentication
        result = authenticate(
            email="user@example.com",
            password="password123"
        )

        logger.info("✓ Authentication successful!")
        logger.info(f"  User ID: {result['user_id']}")
        logger.info(f"  Firebase Token: {result['firebase_id_token'][:30]}...")
        logger.info(f"  JWT Token: {result['jwt_token'][:30]}...")

        # Now you can use the JWT token for API calls
        jwt_token = result['jwt_token']

        # Example: Add to request headers
        import requests
        headers = {"Authorization": f"Bearer {jwt_token}"}

        # Make API call (example)
        # response = requests.get("https://api.example.com/data", headers=headers)

    except ValueError as e:
        logger.error(f"✗ Authentication failed: {e}")


def example_middleware_pattern():
    """
    Example showing middleware-style authentication wrapper.
    """
    logger.info("\n=== Middleware Pattern Example ===\n")

    def require_auth(func):
        """Decorator to require authentication for a function."""
        def wrapper(session: AuthenticatedSession, *args, **kwargs):
            if not session.is_authenticated:
                raise ValueError("Authentication required")

            # Refresh token if needed
            if session.auth.is_token_expired():
                logger.info("Refreshing expired token...")
                session.auth.refresh_id_token()

            return func(session, *args, **kwargs)

        return wrapper

    @require_auth
    def fetch_user_housing_goals(session: AuthenticatedSession):
        """Fetch user's housing goals (requires authentication)."""
        headers = session.get_auth_headers()
        logger.info("Fetching housing goals with authentication...")
        # Make API call here
        return {"goals": ["2-bed house in HP12"]}

    # Usage
    try:
        session = AuthenticatedSession("user@example.com", "password123")
        session.login()

        # This function requires authentication
        goals = fetch_user_housing_goals(session)
        logger.info(f"Retrieved goals: {goals}")

    except ValueError as e:
        logger.error(f"Error: {e}")


def example_with_existing_agents():
    """
    Example showing how to integrate with existing agent system.
    """
    logger.info("\n=== Integration with Existing Agents ===\n")

    # Authenticate first
    try:
        auth = FirebaseAuth()
        result = auth.authenticate_and_get_jwt(
            email="user@example.com",
            password="password123"
        )

        user_id = result['user_id']
        jwt_token = result['jwt_token']

        logger.info(f"✓ Authenticated user: {user_id}")

        # Now you can pass the user_id to your existing agent system
        # Example integration with your existing code:

        # from src.agent.housinggoal import housing_goalagent
        # from google.adk.runners import Runner
        # from google.genai import types

        # runner = Runner(
        #     agent=housing_goalagent,
        #     app_name="housing_deposit_planner",
        #     session_service=session_service
        # )

        # # Include user_id in the session
        # session_id = f"{user_id}_{uuid.uuid4()}"

        # # Add JWT token to metadata for backend calls
        # headers = {"Authorization": f"Bearer {jwt_token}"}

        # # Your existing agent call with authentication context
        # user_content = types.Content(
        #     role='user',
        #     parts=[types.Part(text=json.dumps({"query": "Get housing goals"}))]
        # )

        # async for event in runner.run_async(
        #     user_id=user_id,  # Use authenticated user_id
        #     session_id=session_id,
        #     new_message=user_content
        # ):
        #     # Process events...
        #     pass

    except ValueError as e:
        logger.error(f"Authentication failed: {e}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Firebase Authentication Integration Examples")
    print("="*70)

    # Run examples
    example_simple_auth_flow()
    example_middleware_pattern()
    example_with_existing_agents()

    # Async example
    asyncio.run(example_integration_with_main())

    print("\n" + "="*70)
    print("Integration examples completed")
    print("="*70 + "\n")
