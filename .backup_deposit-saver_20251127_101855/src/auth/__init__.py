"""
Firebase Authentication module for the deposit-saver application.

Provides authentication functionality including:
- Firebase email/password authentication
- Token refresh
- Firebase token to JWT exchange
- Google Cloud Secret Manager integration
"""

from .auth import FirebaseAuth, authenticate
from .secret_manager import (
    SecretManagerClient,
    get_firebase_api_key,
    get_firebase_config_from_secret
)

__all__ = [
    "FirebaseAuth",
    "authenticate",
    "SecretManagerClient",
    "get_firebase_api_key",
    "get_firebase_config_from_secret"
]
