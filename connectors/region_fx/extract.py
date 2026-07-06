import os
import json
import sys
from datetime import datetime
from faker import Faker

fake = Faker()
Faker.seed(33)

REGIONS = [
    {"region_code": "US-EAST", "region_name": "US East", "country": "USA", "currency_code": "USD", "timezone": "America/New_York", "locale": "en_US"},
    {"region_code": "US-WEST", "region_name": "US West", "country": "USA", "currency_code": "USD", "timezone": "America/Los_Angeles", "locale": "en_US"},
    {"region_code": "US-CENTRAL", "region_name": "US Central", "country": "USA", "currency_code": "USD", "timezone": "America/Chicago", "locale": "en_US"},
    {"region_code": "UK-SOUTH", "region_name": "UK South", "country": "United Kingdom", "currency_code": "GBP", "timezone": "Europe/London", "locale": "en_GB"},
    {"region_code": "UK-NORTH", "region_name": "UK North", "country": "United Kingdom", "currency_code": "GBP", "timezone": "Europe/London", "locale": "en_GB"},
    {"region_code": "APAC-INDIA", "region_name": "India", "country": "India", "currency_code": "INR", "timezone": "Asia/Kolkata", "locale": "en_IN"},
    {"region_code": "APAC-UAE", "region_name": "UAE", "country": "United Arab Emirates", "currency_code": "AED", "timezone": "Asia/Dubai", "locale": "ar_AE"},
    {"region_code": "APAC-SG", "region_name": "Singapore", "country": "Singapore", "currency_code": "SGD", "timezone": "Asia/Singapore", "locale": "en_US"},
    {"region_code": "EU-DE", "region_name": "Germany", "country": "Germany", "currency_code": "EUR", "timezone": "Europe/Berlin", "locale": "de_DE"},
    {"region_code": "LATAM-BR", "region_name": "Brazil", "country": "Brazil", "currency_code": "BRL", "timezone": "America/Sao_Paulo", "locale": "pt_BR"}
]

FX_RATES_TO_USD = {
    "USD": 1.0,
    "GBP": 1.27,
    "INR": 0.012,
    "AED": 0.27,
    "SGD": 0.74,
    "EUR": 1.08,
    "BRL": 0.19
}

def main():
    source_name = os.environ.get("SOURCE_NAME", "region_fx")
    output_path = os.environ.get("OUTPUT_PATH", "./output")

    os.makedirs(output_path, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # Write regions
    regions_file = os.path.join(output_path, f"{source_name}_regions_{timestamp}.json")
    with open(regions_file, "w") as f:
        json.dump({
            "source": source_name,
            "entity": "regions",
            "extracted_at": datetime.utcnow().isoformat(),
            "record_count": len(REGIONS),
            "records": REGIONS
        }, f, indent=2)
    print(f"Wrote {len(REGIONS)} regions to {regions_file}")

    # Write FX rates
    fx_records = [{"currency_code": code, "rate_to_usd": rate, "rate_date": datetime.utcnow().strftime("%Y-%m-%d")} for code, rate in FX_RATES_TO_USD.items()]
    fx_file = os.path.join(output_path, f"{source_name}_fx_rates_{timestamp}.json")
    with open(fx_file, "w") as f:
        json.dump({
            "source": source_name,
            "entity": "fx_rates",
            "extracted_at": datetime.utcnow().isoformat(),
            "record_count": len(fx_records),
            "records": fx_records
        }, f, indent=2)
    print(f"Wrote {len(fx_records)} FX rates to {fx_file}")

    print(f"SUCCESS: {len(REGIONS)} regions, {len(fx_records)} FX rates")
    sys.exit(0)

if __name__ == "__main__":
    main()
