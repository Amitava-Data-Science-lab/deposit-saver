import os
import requests
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class FirebaseAuth:
    """
    Firebase Authentication handler for email/password authentication.
    Handles getting Firebase ID tokens and exchanging them for custom JWT tokens.
    """

    def __init__(self, api_key: Optional[str] = None, backend_url: Optional[str] = None,
                 use_secret_manager: bool = True, project_id: Optional[str] = None):
        """
        Initialize Firebase Auth client.

        Args:
            api_key: Firebase Web API key. If not provided, attempts to retrieve from Secret Manager
                    or falls back to FIREBASE_API_KEY env var
            backend_url: Backend URL for JWT token exchange. If not provided, reads from BACKEND_URL env var
            use_secret_manager: If True, attempts to retrieve API key from Google Cloud Secret Manager
            project_id: GCP project ID for Secret Manager (optional, defaults to 485422000664)
        """
        self.api_key = api_key

        # Try to get API key from Secret Manager if enabled and not provided
        if not self.api_key and use_secret_manager:
            try:
                from .secret_manager import get_firebase_api_key
                logger.info("Attempting to retrieve Firebase API key from Secret Manager")
                self.api_key = get_firebase_api_key(project_id=project_id)
                logger.info("Successfully retrieved Firebase API key from Secret Manager")
            except Exception as e:
                logger.warning(f"Failed to retrieve API key from Secret Manager: {e}")
                logger.info("Falling back to environment variable")

        # Fall back to environment variable
        if not self.api_key:
            self.api_key = os.getenv("FIREBASE_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Firebase API key must be provided via:\n"
                "  1. api_key parameter\n"
                "  2. Google Cloud Secret Manager (projects/485422000664/secrets/capstone-project-firebase-config)\n"
                "  3. FIREBASE_API_KEY environment variable"
            )

        self.backend_url = backend_url or os.getenv("BACKEND_URL")

        # Firebase Auth REST API endpoints
        self.sign_in_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
        self.refresh_token_url = f"https://securetoken.googleapis.com/v1/token?key={self.api_key}"

        # Token storage
        self.id_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.user_id: Optional[str] = None
        self.jwt_token: Optional[str] = None

    def get_firebase_token(self, email: str, password: str) -> Dict[str, str]:
        """
        Authenticate with Firebase using email and password to get ID token.

        Args:
            email: User's email address
            password: User's password

        Returns:
            Dict containing:
                - id_token: Firebase ID token
                - refresh_token: Refresh token for getting new ID tokens
                - expires_in: Token expiration time in seconds
                - user_id: Firebase user ID

        Raises:
            requests.HTTPError: If authentication fails
            ValueError: If response is invalid
        """
        logger.info(f"Attempting to authenticate user: {email}")

        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        try:
            response = requests.post(self.sign_in_url, json=payload)
            response.raise_for_status()

            data = response.json()

            # Store tokens and metadata
            self.id_token = data.get("idToken")
            self.refresh_token = data.get("refreshToken")
            expires_in = int(data.get("expiresIn", 3600))
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            self.user_id = data.get("localId")

            logger.info(f"Successfully authenticated user: {email} (User ID: {self.user_id})")

            return {
                "id_token": self.id_token,
                "refresh_token": self.refresh_token,
                "expires_in": str(expires_in),
                "user_id": self.user_id
            }

        except requests.HTTPError as e:
            error_message = e.response.json().get("error", {}).get("message", "Unknown error")
            logger.error(f"Firebase authentication failed: {error_message}")
            raise ValueError(f"Firebase authentication failed: {error_message}") from e

    def refresh_id_token(self) -> Dict[str, str]:
        """
        Refresh the Firebase ID token using the refresh token.

        Returns:
            Dict containing new id_token, refresh_token, and expires_in

        Raises:
            ValueError: If no refresh token is available or refresh fails
        """
        if not self.refresh_token:
            raise ValueError("No refresh token available. Please authenticate first.")

        logger.info("Refreshing Firebase ID token")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }

        try:
            response = requests.post(self.refresh_token_url, json=payload)
            response.raise_for_status()

            data = response.json()

            # Update tokens
            self.id_token = data.get("id_token")
            self.refresh_token = data.get("refresh_token")
            expires_in = int(data.get("expires_in", 3600))
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            self.user_id = data.get("user_id")

            logger.info("Successfully refreshed Firebase ID token")

            return {
                "id_token": self.id_token,
                "refresh_token": self.refresh_token,
                "expires_in": str(expires_in),
                "user_id": self.user_id
            }

        except requests.HTTPError as e:
            error_message = e.response.json().get("error", {}).get("message", "Unknown error")
            logger.error(f"Token refresh failed: {error_message}")
            raise ValueError(f"Token refresh failed: {error_message}") from e

    def exchange_for_jwt(self, firebase_token: Optional[str] = None, jwt_exchange_endpoint: Optional[str] = None) -> Dict[str, str]:
        """
        Exchange Firebase ID token for a custom JWT token from your backend.

        Args:
            firebase_token: Firebase ID token to exchange. If not provided, uses stored token
            jwt_exchange_endpoint: Backend endpoint for token exchange. If not provided, uses
                                   BACKEND_URL/auth/exchange or provided backend_url

        Returns:
            Dict containing:
                - jwt_token: Custom JWT token from backend
                - expires_in: Token expiration time (if provided by backend)

        Raises:
            ValueError: If no Firebase token is available or backend URL not configured
            requests.HTTPError: If token exchange fails
        """
        token = firebase_token or self.id_token

        if not token:
            raise ValueError("No Firebase token available. Please authenticate first.")

        # Determine the exchange endpoint
        if jwt_exchange_endpoint:
            exchange_url = jwt_exchange_endpoint
        elif self.backend_url:
            exchange_url = f"{self.backend_url.rstrip('/')}/auth/exchange"
        else:
            raise ValueError("Backend URL must be provided or set in BACKEND_URL environment variable")

        logger.info(f"Exchanging Firebase token for JWT at {exchange_url}")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(exchange_url, headers=headers)
            response.raise_for_status()

            data = response.json()

            # Store JWT token
            self.jwt_token = data.get("jwt_token") or data.get("token") or data.get("access_token")

            if not self.jwt_token:
                raise ValueError("Backend did not return a JWT token in expected format")

            logger.info("Successfully exchanged Firebase token for JWT")

            return {
                "jwt_token": self.jwt_token,
                "expires_in": data.get("expires_in", ""),
                "token_type": data.get("token_type", "Bearer")
            }

        except requests.HTTPError as e:
            error_detail = "Unknown error"
            try:
                error_detail = e.response.json().get("error", e.response.text)
            except:
                error_detail = e.response.text

            logger.error(f"JWT exchange failed: {error_detail}")
            raise ValueError(f"JWT exchange failed: {error_detail}") from e

    def authenticate_and_get_jwt(self, email: str, password: str, jwt_exchange_endpoint: Optional[str] = None) -> Dict[str, str]:
        """
        Complete authentication flow: Get Firebase token and exchange for JWT.

        Args:
            email: User's email address
            password: User's password
            jwt_exchange_endpoint: Optional custom endpoint for JWT exchange

        Returns:
            Dict containing both Firebase and JWT tokens:
                - firebase_id_token: Firebase ID token
                - firebase_refresh_token: Firebase refresh token
                - jwt_token: Custom JWT token
                - user_id: Firebase user ID

        Raises:
            ValueError: If authentication or exchange fails
        """
        logger.info(f"Starting complete authentication flow for user: {email}")

        # Step 1: Get Firebase token
        firebase_result = self.get_firebase_token(email, password)

        # Step 2: Exchange for JWT
        jwt_result = self.exchange_for_jwt(jwt_exchange_endpoint=jwt_exchange_endpoint)

        logger.info("Complete authentication flow successful")

        return {
            "firebase_id_token": firebase_result["id_token"],
            "firebase_refresh_token": firebase_result["refresh_token"],
            "jwt_token": jwt_result["jwt_token"],
            "user_id": firebase_result["user_id"],
            "firebase_expires_in": firebase_result["expires_in"],
            "jwt_token_type": jwt_result.get("token_type", "Bearer")
        }

    def is_token_expired(self) -> bool:
        """
        Check if the current Firebase ID token is expired.

        Returns:
            True if token is expired or not set, False otherwise
        """
        if not self.token_expiry:
            return True
        return datetime.now() >= self.token_expiry

    def get_auth_header(self, use_jwt: bool = True) -> Dict[str, str]:
        """
        Get authorization header for API requests.

        Args:
            use_jwt: If True, uses JWT token. If False, uses Firebase ID token

        Returns:
            Dict with Authorization header

        Raises:
            ValueError: If requested token is not available
        """
        if use_jwt:
            if not self.jwt_token:
                raise ValueError("No JWT token available. Please authenticate first.")
            return {"Authorization": f"Bearer {self.jwt_token}"}
        else:
            if not self.id_token:
                raise ValueError("No Firebase ID token available. Please authenticate first.")
            return {"Authorization": f"Bearer {self.id_token}"}


# Convenience function for quick authentication
def authenticate(email: str, password: str,
                api_key: Optional[str] = None,
                backend_url: Optional[str] = None,
                jwt_exchange_endpoint: Optional[str] = None,
                use_secret_manager: bool = True,
                project_id: Optional[str] = None) -> Dict[str, str]:
    """
    Convenience function for complete authentication flow.

    Args:
        email: User's email address
        password: User's password
        api_key: Firebase Web API key (optional, retrieves from Secret Manager or env)
        backend_url: Backend URL (optional, reads from env)
        jwt_exchange_endpoint: Custom JWT exchange endpoint (optional)
        use_secret_manager: If True, attempts to retrieve API key from Secret Manager
        project_id: GCP project ID for Secret Manager (optional)

    Returns:
        Dict containing all tokens and user information
    """
    auth_client = FirebaseAuth(
        api_key=api_key,
        backend_url=backend_url,
        use_secret_manager=use_secret_manager,
        project_id=project_id
    )
    return auth_client.authenticate_and_get_jwt(email, password, jwt_exchange_endpoint)
