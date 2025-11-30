import logging
import json
import os
from google.cloud import storage
from typing import List, Dict, Any

logger = logging.getLogger(__name__)
HOUSE_PRICE_BUCKET="capstone-project-house-price-cache"


def save_house_price_to_gcs(
    postcode: str,
    property_type: str,
    house_price_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Save house price JSON array to a GCP bucket in the 'house_price' folder.

    Args:
        postcode: The postcode for the property (e.g., "SW1A 1AA")
        property_type: The type of property (e.g., "detached", "semi-detached", "terraced", "flat")
        house_price_data: List of house price data dictionaries to save as JSON
       
    Returns:
        Dict containing:
            - status: "success" or "error"
            - file_path: GCS path to the saved file (if successful)
            - message: Description of the result

    Example:
        >>> result = save_house_price_to_gcs(
        ...     postcode="SW1A 1AA",
        ...     property_type="detached",
        ...     house_price_data=[{"price": 500000, "date": "2024-01-01"}]
        ... )
        >>> print(result)
        {'status': 'success', 'file_path': 'gs://bucket/house_price/SW1A_1AA_detached.json', 'message': 'Successfully saved house price data'}
    """
    logger.info(f"=== Starting save_house_price_to_gcs ===")
    logger.info(f"Input: postcode='{postcode}', property_type='{property_type}', data_count={len(house_price_data) if house_price_data else 0}")
    bucket_name = os.getenv("HOUSE_PRICE_BUCKET", HOUSE_PRICE_BUCKET)
    try:
        # Get bucket name from environment if not provided
        if bucket_name is None:
            logger.debug("No bucket_name provided, using environment variable or default")
            bucket_name = os.getenv("HOUSE_PRICE_BUCKET", HOUSE_PRICE_BUCKET)
            if not bucket_name:
                logger.error("GCS bucket name not provided and HOUSE_PRICE_BUCKET env variable not set")
                return {
                    "status": "error",
                    "file_path": None,
                    "message": "GCS bucket name not configured. Set HOUSE_PRICE_BUCKET environment variable."
                }

        logger.info(f"Using GCS bucket: {bucket_name}")

        # Sanitize postcode and property_type for filename
        # Remove spaces and special characters from postcode
        sanitized_postcode = postcode.lower().replace(" ", "_").replace("/", "_").replace("\\", "_")
        sanitized_property_type = property_type.lower().replace(" ", "_").replace("/", "_")
        logger.debug(f"Sanitized filename components: postcode='{sanitized_postcode}', property_type='{sanitized_property_type}'")

        # Create filename: postcode_propertytype.json
        filename = f"{sanitized_postcode}_{sanitized_property_type}.json"

        # Create blob path in 'house_price' folder
        blob_path = f"house_price/{filename}"
        logger.info(f"Target blob path: {blob_path}")

        # Initialize storage client
        logger.debug("Initializing GCS storage client")
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        # Convert data to JSON string
        json_data = json.dumps(house_price_data, indent=2)
        data_size_kb = len(json_data) / 1024
        logger.debug(f"JSON data size: {data_size_kb:.2f} KB")

        # Upload to GCS
        logger.info(f"Uploading to GCS: {blob_path}")
        blob.upload_from_string(
            json_data,
            content_type="application/json"
        )

        gcs_path = f"gs://{bucket_name}/{blob_path}"
        logger.info(f"✓ Successfully saved house price data to: {gcs_path}")

        return {
            "status": "success",
            "file_path": gcs_path,
            "message": f"Successfully saved house price data for {postcode} ({property_type})"
        }

    except Exception as e:
        logger.error(f"Error saving house price data to GCS: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "file_path": None,
            "message": f"Failed to save house price data: {str(e)}"
        }


def load_house_price_from_gcs(
    postcode: str,
    property_type: str
) -> Dict[str, Any]:
    """
    Load house price JSON array from GCP bucket.

    Args:
        postcode: The postcode for the property
        property_type: The type of property

    Returns:
        Dict containing:
            - status: "success" or "error"
            - data: List of house price data (if successful)
            - message: Description of the result
    """
    logger.info(f"=== Starting load_house_price_from_gcs ===")
    logger.info(f"Input: postcode='{postcode}', property_type='{property_type}'")
    bucket_name = os.getenv("HOUSE_PRICE_BUCKET", HOUSE_PRICE_BUCKET)
    try:
        # Get bucket name from environment if not provided
        if bucket_name is None:
            logger.debug("No bucket_name provided, using environment variable or default")
            bucket_name = os.getenv("HOUSE_PRICE_BUCKET", HOUSE_PRICE_BUCKET)
            if not bucket_name:
                logger.error("GCS bucket name not provided and HOUSE_PRICE_BUCKET env variable not set")
                return {
                    "status": "error",
                    "data": None,
                    "message": "GCS bucket name not configured. Set HOUSE_PRICE_BUCKET environment variable."
                }

        logger.info(f"Using GCS bucket: {bucket_name}")

        # Sanitize postcode and property_type for filename
        sanitized_postcode = postcode.lower().replace(" ", "_").replace("/", "_").replace("\\", "_")
        sanitized_property_type = property_type.lower().replace(" ", "_").replace("/", "_")
        logger.debug(f"Sanitized filename components: postcode='{sanitized_postcode}', property_type='{sanitized_property_type}'")

        # Create filename
        filename = f"{sanitized_postcode}_{sanitized_property_type}.json"
        blob_path = f"house_price/{filename}"
        logger.info(f"Looking for blob path: {blob_path}")

        # Initialize storage client
        logger.debug("Initializing GCS storage client")
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        # Check if file exists
        logger.debug("Checking if blob exists in GCS")
        if not blob.exists():
            logger.warning(f"✗ House price data not found in cache: {blob_path}")
            return {
                "status": "error",
                "house_price_data": None,
                "message": f"No cached data found for {postcode} ({property_type})"
            }

        # Download and parse JSON
        logger.info(f"Downloading data from GCS: {blob_path}")
        json_data = blob.download_as_string()
        data_size_kb = len(json_data) / 1024
        logger.debug(f"Downloaded data size: {data_size_kb:.2f} KB")

        house_price_data = json.loads(json_data)
        logger.debug(f"Parsed JSON data: {len(house_price_data)} records")

        logger.info(f"✓ Successfully loaded house price data from: gs://{bucket_name}/{blob_path}")

        return {
            "status": "success",
            "house_price_data": house_price_data,
            "message": f"Successfully loaded cached house price data for {postcode} ({property_type})"
        }

    except Exception as e:
        logger.error(f"Error loading house price data from GCS: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "data": None,
            "message": f"Failed to load house price data: {str(e)}"
        }
