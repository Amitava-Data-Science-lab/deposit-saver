import logging

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