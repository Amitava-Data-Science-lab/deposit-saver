from src.tools.HousePriceCache import save_house_price_to_gcs, load_house_price_from_gcs    


def main():
    """Sample house price data for testing"""
    sample_data =  [
        {
            "price": 500000,
            "date": "2024-01-01",
            "address": "123 Main Street",
            "bedrooms": 3
        },
        {
            "price": 520000,
            "date": "2024-02-01",
            "address": "456 Oak Avenue",
            "bedrooms": 4
        }
    ]
    save_response = save_house_price_to_gcs(
        postcode="SW1A",
        property_type="detached",
        house_price_data=sample_data )
    print(f"Save response: {save_response}")
    
    load_response = load_house_price_from_gcs(
        postcode="SW1A",
        property_type="detached")
    print(f"Load response: {load_response}")


if __name__ == "__main__":
    main()