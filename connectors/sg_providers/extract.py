import os
import json
import sys
from datetime import datetime
from faker import Faker

fake = Faker()
Faker.seed(888)

SPECIALTIES = [
    "General Practitioner", "Cardiologist", "Dermatologist",
    "Orthopedic Surgeon", "Pediatrician", "Neurologist",
    "Oncologist", "Psychiatrist", "Ophthalmologist", "ENT Specialist"
]

def generate_providers(count=50):
    providers = []
    for i in range(count):
        issue_date = fake.date_between(start_date="-5y", end_date="-1y")
        expiration_date = fake.date_between(start_date="-30d", end_date="+365d")
        providers.append({
            "npi": f"SG-{10000 + i}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "credential": fake.random_element(["MD", "MBBS", "DO", "MRCP"]),
            "gender": fake.random_element(["Male", "Female"]),
            "specialty": fake.random_element(SPECIALTIES),
            "taxonomy_code": f"SG-TAX-{fake.random_int(100, 999)}",
            "license_number": f"SMC-{fake.random_int(10000, 99999)}",
            "license_issue_date": issue_date.isoformat(),
            "license_expiration_date": expiration_date.isoformat(),
            "state": "Singapore",
            "practice_city": fake.random_element(["Singapore Central", "Jurong", "Tampines", "Woodlands", "Bedok"]),
            "practice_state": "Singapore",
            "practice_zip": fake.postcode(),
            "enumeration_date": fake.date_between(start_date="-10y", end_date="-1y").isoformat(),
            "last_updated": fake.date_between(start_date="-6m", end_date="today").isoformat(),
            "status": "A"
        })
    return providers

def main():
    source_name = os.environ.get("SOURCE_NAME", "sg_providers")
    output_path = os.environ.get("OUTPUT_PATH", "./output")
    count = int(os.environ.get("SG_PROVIDER_COUNT", "50"))

    os.makedirs(output_path, exist_ok=True)

    print(f"Generating {count} Singapore provider records...")
    providers = generate_providers(count)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_path, f"{source_name}_{timestamp}.json")

    with open(output_file, "w") as f:
        json.dump({
            "source": source_name,
            "extracted_at": datetime.utcnow().isoformat(),
            "record_count": len(providers),
            "records": providers
        }, f, indent=2)

    print(f"SUCCESS: Wrote {len(providers)} providers to {output_file}")
    sys.exit(0)

if __name__ == "__main__":
    main()
