import logging
import requests
import json

logger = logging.getLogger(__name__)

def property_price_search(postcode: str, property_type: str) -> float:
    """
    Search for property prices based on UK postcode and property type.

    Args:
        postcode: UK postcode prefix (e.g., "SW1", "HP12")
        property_type: Type of property (e.g., "1-bed flat", "2-bed flat", "2-bed house", "3-bed house")

    Returns:
        Estimated property price in GBP
    """
    logger.info(f"Searching property price for postcode={postcode}, property_type={property_type}")

    if property_type == "1-bed flat":
        price = 100000
    elif property_type == "2-bed flat":
        price = 200000
    elif property_type == "2-bed house":
        price = 300000
    elif property_type == "3-bed house":
        price = 400000
    else:
        logger.warning(f"Unknown property_type: {property_type}, returning 0")
        price = 0

    logger.info(f"Property price found: {price}")
    return price


def outcode_checker(outcode: str) -> dict:
    """
    Check if a UK outcode (postcode prefix) is valid and retrieve its details.

    Args:
        outcode: UK outcode (e.g., "HP12", "SW1")

    Returns:
        dict: Response containing:
            - status: "success" or "error"
            - message: Error message if status is "error"
            - data: Outcode details if status is "success"
    """
    output = {
        "status": "error",
        "message": "",
        "data": None
    }
    uri = f"https://api.postcodes.io/outcodes/{outcode}"

    try:
        logger.info(f"Checking outcode: {outcode}")
        r = requests.get(uri)

        if r.status_code == 200:
            response_body = json.loads(r.text)
            logger.info(f"API response: {response_body}")

            if response_body.get("status") == 200:
                output["status"] = "success"
                output["data"] = response_body.get("result", {})
                output["message"] = f"Outcode {outcode} found successfully"
                logger.info(f"Outcode {outcode} is valid")
            else:
                output["message"] = f"Outcode {outcode} doesn't exist"
                logger.warning(f"Outcode {outcode} not found in API")
        else:
            output["message"] = f"Unable to find the outcode {outcode} (HTTP {r.status_code})"
            logger.error(f"API returned status code {r.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while checking outcode {outcode}: {e}")
        output["message"] = f"Network error: Unable to check outcode {outcode}"
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for outcode {outcode}: {e}")
        output["message"] = f"Invalid response format from API"
    except Exception as e:
        logger.error(f"Unexpected error checking outcode {outcode}: {e}")
        output["message"] = f"Unexpected error: {str(e)}"

    return output


def nearby_outcodes(outcode: str) -> dict:
    """
    Check if a UK outcode (postcode prefix) is valid and retrieve its details.

    Args:
        outcode: UK outcode (e.g., "HP12", "SW1")
        
    Returns:
        dict: Response containing:
            - status: "success" or "error"
            - message: Error message if status is "error"
            - data: Outcode details if status is "success"
    """
    output = {
        "status": "error",
        "message": "",
        "nearby_postcodes": []
    }
    
    uri = f"https://api.postcodes.io/outcodes/{outcode}/nearest"

    try:
        
        r = requests.get(uri)

        if r.status_code == 200:
            response_body = json.loads(r.text)
            logger.info(f"API response: {response_body}")

            if response_body.get("status") == 200:
                output["status"] = "success"
                codes = []
                for item in response_body.get("result", []):
                    if item.get("outcode") != outcode:
                        codes.append(item.get("outcode"))
                if len(codes) >0:
                    output["message"] = "Nearby Postcodes found"
                else:
                    output["message"] = "No nearby postcodes found"

                output["nearby_postcodes"] = codes
                logger.info(f"Outcode {outcode} is valid")
            else:
                output["message"] = f"Outcode {outcode} doesn't exist"
                logger.warning(f"Outcode {outcode} not found in API")
        else:
            output["message"] = f"Unable to find the outcode {outcode} (HTTP {r.status_code})"
            logger.error(f"API returned status code {r.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while checking outcode {outcode}: {e}")
        output["message"] = f"Network error: Unable to check outcode {outcode}"
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for outcode {outcode}: {e}")
        output["message"] = f"Invalid response format from API"
    except Exception as e:
        logger.error(f"Unexpected error checking outcode {outcode}: {e}")
        output["message"] = f"Unexpected error: {str(e)}"

    return output