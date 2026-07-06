import os
import json
import requests
import sys
from datetime import datetime
from faker import Faker

fake = Faker()
Faker.seed(42)

STATE_CITIES = {
    "OH": ["Columbus", "Cleveland", "Cincinnati"],
    "CA": ["Los Angeles", "San Francisco", "San Diego"],
    "NY": ["New York", "Buffalo", "Albany"],
    "TX": ["Houston", "Dallas", "Austin"],
    "FL": ["Miami", "Orlando", "Tampa"]
}

def generate_license_dates():
    """Generate realistic license issue and expiration dates."""
    issue_date = fake.date_between(start_date="-5y", end_date="-1y")
    expiration_date = fake.date_between(start_date="-30d", end_date="+365d")
    return issue_date.isoformat(), expiration_date.isoformat()

def extract_providers(state, city, limit=20):
    base_url = "https://npiregistry.cms.hhs.gov/api/"
    params = {
        "version": "2.1",
        "city": city,
        "state": state,
        "limit": limit,
        "enumeration_type": "NPI-1"
    }

    print(f"Extracting providers: {city}, {state} (limit {limit})")
    response = requests.get(base_url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])
    print(f"  Retrieved {len(results)} records")

    providers = []
    for r in results:
        basic = r.get("basic", {})
        addresses = r.get("addresses", [{}])
        taxonomies = r.get("taxonomies", [{}])

        practice_address = {}
        for addr in addresses:
            if addr.get("address_purpose") == "LOCATION":
                practice_address = addr
                break
        if not practice_address and addresses:
            practice_address = addresses[0]

        primary_taxonomy = {}
        for tax in taxonomies:
            if tax.get("primary") == True:
                primary_taxonomy = tax
                break
        if not primary_taxonomy and taxonomies:
            primary_taxonomy = taxonomies[0]

        license_issue_date, license_expiration_date = generate_license_dates()

        providers.append({
            "npi": r.get("number"),
            "first_name": basic.get("first_name", ""),
            "last_name": basic.get("last_name", ""),
            "credential": basic.get("credential", ""),
            "gender": basic.get("gender", ""),
            "specialty": primary_taxonomy.get("desc", ""),
            "taxonomy_code": primary_taxonomy.get("code", ""),
            "license_number": primary_taxonomy.get("license", ""),
            "license_issue_date": license_issue_date,
            "license_expiration_date": license_expiration_date,
            "state": primary_taxonomy.get("state", ""),
            "practice_city": practice_address.get("city", ""),
            "practice_state": practice_address.get("state", ""),
            "practice_zip": practice_address.get("postal_code", ""),
            "enumeration_date": basic.get("enumeration_date", ""),
            "last_updated": basic.get("last_updated", ""),
            "status": basic.get("status", "A")
        })

    return providers


def main():
    source_name = os.environ.get("SOURCE_NAME", "npi_registry")
    output_path = os.environ.get("OUTPUT_PATH", "./output")
    limit_per_city = int(os.environ.get("NPI_LIMIT_PER_CITY", "20"))

    os.makedirs(output_path, exist_ok=True)

    all_providers = []
    for state, cities in STATE_CITIES.items():
        for city in cities:
            try:
                providers = extract_providers(state, city, limit=limit_per_city)
                all_providers.extend(providers)
            except requests.exceptions.RequestException as e:
                print(f"ERROR extracting {city}, {state}: {e}", file=sys.stderr)
                sys.exit(1)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_path, f"{source_name}_{timestamp}.json")

    with open(output_file, "w") as f:
        json.dump({
            "source": source_name,
            "extracted_at": datetime.utcnow().isoformat(),
            "record_count": len(all_providers),
            "records": all_providers
        }, f, indent=2)

    print(f"SUCCESS: Wrote {len(all_providers)} records to {output_file}")
    sys.exit(0)


if __name__ == "__main__":
    main()
