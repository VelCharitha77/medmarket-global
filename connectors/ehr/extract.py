import os
import json
import requests
import sys
from datetime import datetime

def fetch_all_pages(base_url, endpoint, limit=100):
    """Paginate through an API endpoint, following 'next' links until exhausted."""
    all_results = []
    url = f"{base_url}{endpoint}?limit={limit}&offset=0"

    while url:
        print(f"  Fetching: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        all_results.extend(data["results"])

        next_path = data.get("next")
        if next_path:
            url = f"{base_url}{next_path}"
        else:
            url = None

    return all_results

def main():
    source_name = os.environ.get("SOURCE_NAME", "ehr")
    output_path = os.environ.get("OUTPUT_PATH", "./output")
    ehr_api_url = os.environ.get("EHR_API_URL", "http://localhost:5000")

    os.makedirs(output_path, exist_ok=True)

    try:
        # Extract patients
        print("Extracting patients...")
        patients = fetch_all_pages(ehr_api_url, "/api/patients", limit=100)
        print(f"  Total patients: {len(patients)}")

        # Extract encounters (appointments/bookings)
        print("Extracting encounters...")
        encounters = fetch_all_pages(ehr_api_url, "/api/encounters", limit=200)
        print(f"  Total encounters: {len(encounters)}")

    except requests.exceptions.RequestException as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # Write patients
    patients_file = os.path.join(output_path, f"{source_name}_patients_{timestamp}.json")
    with open(patients_file, "w") as f:
        json.dump({
            "source": source_name,
            "entity": "patients",
            "extracted_at": datetime.utcnow().isoformat(),
            "record_count": len(patients),
            "records": patients
        }, f, indent=2)
    print(f"Wrote patients to {patients_file}")

    # Write encounters
    encounters_file = os.path.join(output_path, f"{source_name}_encounters_{timestamp}.json")
    with open(encounters_file, "w") as f:
        json.dump({
            "source": source_name,
            "entity": "encounters",
            "extracted_at": datetime.utcnow().isoformat(),
            "record_count": len(encounters),
            "records": encounters
        }, f, indent=2)
    print(f"Wrote encounters to {encounters_file}")

    print(f"SUCCESS: {len(patients)} patients, {len(encounters)} encounters")
    sys.exit(0)

if __name__ == "__main__":
    main()
