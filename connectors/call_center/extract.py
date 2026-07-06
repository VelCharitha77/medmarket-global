import os
import json
import sys
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
Faker.seed(55)
random.seed(55)

REGIONS = ["US-East", "US-West", "US-Central", "UK-South", "APAC-India", "APAC-UAE"]
CALL_TYPES = ["inbound", "inbound", "inbound", "outbound"]
DISPOSITIONS = ["resolved", "resolved", "resolved", "escalated", "abandoned", "voicemail"]
TOPICS = ["appointment_scheduling", "billing_inquiry", "prescription_refill", "insurance_verification", "complaint", "general_inquiry", "provider_lookup"]

def generate_calls(count=1000):
    calls = []
    for i in range(count):
        call_start = fake.date_time_between(start_date="-90d", end_date="now")
        wait_seconds = max(0, int(random.gauss(120, 90)))
        duration_seconds = max(30, int(random.gauss(300, 150)))
        disposition = fake.random_element(DISPOSITIONS)

        if disposition == "abandoned":
            duration_seconds = wait_seconds
            wait_seconds = max(180, int(random.gauss(300, 100)))

        calls.append({
            "call_id": f"call-{100000 + i}",
            "call_start_time": call_start.isoformat(),
            "call_end_time": (call_start + timedelta(seconds=wait_seconds + duration_seconds)).isoformat(),
            "wait_time_seconds": wait_seconds,
            "call_duration_seconds": duration_seconds,
            "region": fake.random_element(REGIONS),
            "call_type": fake.random_element(CALL_TYPES),
            "topic": fake.random_element(TOPICS),
            "disposition": disposition,
            "is_resolved": disposition == "resolved",
            "agent_id": f"agent-{fake.random_int(min=100, max=150)}",
            "customer_phone": fake.phone_number(),
            "satisfaction_score": fake.random_int(min=1, max=5) if disposition == "resolved" else None
        })
    return calls

def main():
    source_name = os.environ.get("SOURCE_NAME", "call_center")
    output_path = os.environ.get("OUTPUT_PATH", "./output")
    call_count = int(os.environ.get("CALL_COUNT", "1000"))

    os.makedirs(output_path, exist_ok=True)

    print(f"Generating {call_count} call records...")
    calls = generate_calls(call_count)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_path, f"{source_name}_{timestamp}.json")

    with open(output_file, "w") as f:
        json.dump({
            "source": source_name,
            "extracted_at": datetime.utcnow().isoformat(),
            "record_count": len(calls),
            "records": calls
        }, f, indent=2)

    print(f"SUCCESS: Wrote {len(calls)} calls to {output_file}")
    sys.exit(0)

if __name__ == "__main__":
    main()
