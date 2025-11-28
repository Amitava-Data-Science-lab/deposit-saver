"""
Google Cloud Secret Manager integration for Firebase configuration.
"""

import json
import logging
import os
from typing import Dict, Optional
from google.cloud import secretmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class SecretManagerClient:
    """
    Client for accessing secrets stored in Google Cloud Secret Manager.
    Configuration is loaded from .env file.
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Secret Manager client.

        Args:
            project_id: GCP project ID. If not provided, reads from FIREBASE_SECRET_PROJECT_ID env var
        """
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id or os.getenv("FIREBASE_SECRET_PROJECT_ID", "485422000664")

    def get_secret(self, secret_name: str, version: str = "latest") -> str:
        """
        Retrieve a secret from Google Cloud Secret Manager.

        Args:
            secret_name: Name of the secret (e.g., 'capstone-project-firebase-config')
            version: Version of the secret (default: 'latest')

        Returns:
            Secret value as string

        Raises:
            Exception: If secret cannot be retrieved
        """
        secret_path = f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"

        try:
            logger.info(f"Fetching secret: {secret_path}")
            response = self.client.access_secret_version(name=secret_path)
            secret_value = response.payload.data.decode('UTF-8')
            logger.info(f"Successfully retrieved secret: {secret_name}")
            return secret_value

        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise

    def get_firebase_config(self, secret_name: Optional[str] = None, version: Optional[str] = None) -> Dict[str, str]:
        """
        Retrieve Firebase configuration from Secret Manager.
        Reads secret name and version from .env file if not provided.

        Args:
            secret_name: Name of the secret containing Firebase config JSON.
                        If not provided, reads from FIREBASE_SECRET_NAME env var
            version: Secret version. If not provided, reads from FIREBASE_SECRET_VERSION env var

        Returns:
            Dict containing Firebase configuration with keys like:
                - apiKey
                - authDomain
                - projectId
                - storageBucket
                - messagingSenderId
                - appId

        Raises:
            json.JSONDecodeError: If secret is not valid JSON
            Exception: If secret cannot be retrieved
        """
        secret_name = secret_name or os.getenv("FIREBASE_SECRET_NAME", "capstone-project-firebase-config")
        version = version or os.getenv("FIREBASE_SECRET_VERSION", "latest")

        logger.info(f"Retrieving Firebase config from secret: {secret_name} (version: {version})")

        secret_value = self.get_secret(secret_name, version)

        try:
            config = json.loads(secret_value)
            logger.info("Successfully parsed Firebase configuration")

            # Validate that apiKey exists
            if "apiKey" not in config:
                logger.warning("Firebase config does not contain 'apiKey' field")

            return config

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Firebase config JSON: {e}")
            raise ValueError(f"Invalid JSON in Firebase config secret: {e}") from e


def get_firebase_api_key(project_id: Optional[str] = None,
                         secret_name: Optional[str] = None,
                         version: Optional[str] = None) -> str:
    """
    Convenience function to get just the Firebase API key.
    Reads configuration from .env file if parameters not provided.

    Args:
        project_id: GCP project ID (optional, reads from FIREBASE_SECRET_PROJECT_ID env var)
        secret_name: Name of the secret containing Firebase config (optional, reads from FIREBASE_SECRET_NAME env var)
        version: Secret version (optional, reads from FIREBASE_SECRET_VERSION env var)

    Returns:
        Firebase API key string

    Raises:
        ValueError: If apiKey not found in config
        Exception: If secret cannot be retrieved
    """
    client = SecretManagerClient(project_id=project_id)
    config = client.get_firebase_config(secret_name=secret_name, version=version)

    api_key = config.get("apiKey")

    if not api_key:
        raise ValueError("Firebase config does not contain 'apiKey' field")

    return api_key


def get_firebase_config_from_secret(project_id: Optional[str] = None,
                                    secret_name: Optional[str] = None,
                                    version: Optional[str] = None) -> Dict[str, str]:
    """
    Convenience function to get complete Firebase configuration.
    Reads configuration from .env file if parameters not provided.

    Args:
        project_id: GCP project ID (optional, reads from FIREBASE_SECRET_PROJECT_ID env var)
        secret_name: Name of the secret containing Firebase config (optional, reads from FIREBASE_SECRET_NAME env var)
        version: Secret version (optional, reads from FIREBASE_SECRET_VERSION env var)

    Returns:
        Dict containing complete Firebase configuration
    """
    client = SecretManagerClient(project_id=project_id)
    return client.get_firebase_config(secret_name=secret_name, version=version)
