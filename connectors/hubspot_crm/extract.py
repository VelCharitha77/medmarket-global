import os
import json
import sys
from datetime import datetime
from faker import Faker

fake = Faker()
Faker.seed(99)

LIFECYCLE_STAGES = ["subscriber", "lead", "marketingqualifiedlead", "salesqualifiedlead", "opportunity", "customer"]
LEAD_SOURCES = ["organic_search", "paid_search", "social_media", "referral", "direct", "email_campaign"]
REGIONS = ["US-East", "US-West", "US-Central", "UK-South", "UK-North", "APAC-India", "APAC-UAE"]

def generate_contacts(count=200):
    contacts = []
    for i in range(count):
        created = fake.date_time_between(start_date="-2y", end_date="now")
        contacts.append({
            "contact_id": f"hs-{10000 + i}",
            "email": fake.email(),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "company": fake.company(),
            "phone": fake.phone_number(),
            "lifecycle_stage": fake.random_element(LIFECYCLE_STAGES),
            "lead_source": fake.random_element(LEAD_SOURCES),
            "region": fake.random_element(REGIONS),
            "created_at": created.isoformat(),
            "last_activity_date": fake.date_time_between(start_date=created, end_date="now").isoformat(),
            "is_active": fake.boolean(chance_of_getting_true=80)
        })
    return contacts

def main():
    source_name = os.environ.get("SOURCE_NAME", "hubspot_crm")
    output_path = os.environ.get("OUTPUT_PATH", "./output")
    contact_count = int(os.environ.get("HUBSPOT_CONTACT_COUNT", "200"))

    os.makedirs(output_path, exist_ok=True)

    print(f"Generating {contact_count} CRM contacts...")
    contacts = generate_contacts(contact_count)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_path, f"{source_name}_{timestamp}.json")

    with open(output_file, "w") as f:
        json.dump({
            "source": source_name,
            "extracted_at": datetime.utcnow().isoformat(),
            "record_count": len(contacts),
            "records": contacts
        }, f, indent=2)

    print(f"SUCCESS: Wrote {len(contacts)} contacts to {output_file}")
    sys.exit(0)

if __name__ == "__main__":
    main()
