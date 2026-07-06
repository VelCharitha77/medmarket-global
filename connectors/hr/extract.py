import os
import json
import sys
from datetime import datetime
from faker import Faker

fake = Faker()
Faker.seed(77)

DEPARTMENTS = ["Engineering", "Clinical Operations", "Finance", "HR", "Sales", "Marketing", "Call Center", "Credentialing"]
JOB_TITLES = {
    "Engineering": ["Data Engineer", "Software Engineer", "DevOps Engineer", "QA Engineer"],
    "Clinical Operations": ["Nurse Practitioner", "Medical Assistant", "Clinical Coordinator", "Care Manager"],
    "Finance": ["Financial Analyst", "Accountant", "Billing Specialist", "Revenue Cycle Manager"],
    "HR": ["HR Generalist", "Recruiter", "Benefits Coordinator", "HR Manager"],
    "Sales": ["Account Executive", "Sales Manager", "Business Development Rep", "Sales Director"],
    "Marketing": ["Marketing Analyst", "Content Specialist", "Campaign Manager", "Marketing Director"],
    "Call Center": ["Call Center Agent", "Team Lead", "Quality Analyst", "Call Center Manager"],
    "Credentialing": ["Credentialing Specialist", "Compliance Analyst", "Credentialing Manager"]
}
EMPLOYMENT_STATUSES = ["active", "active", "active", "active", "on_leave", "terminated"]
REGIONS = ["US-East", "US-West", "US-Central", "UK-South", "APAC-India", "APAC-UAE"]

def generate_employees(count=500):
    employees = []
    for i in range(count):
        dept = fake.random_element(DEPARTMENTS)
        hire_date = fake.date_between(start_date="-10y", end_date="-30d")
        status = fake.random_element(EMPLOYMENT_STATUSES)
        term_date = None
        if status == "terminated":
            term_date = fake.date_between(start_date=hire_date, end_date="today").isoformat()

        employees.append({
            "employee_id": f"emp-{1000 + i}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.company_email(),
            "department": dept,
            "job_title": fake.random_element(JOB_TITLES[dept]),
            "region": fake.random_element(REGIONS),
            "hire_date": hire_date.isoformat(),
            "termination_date": term_date,
            "employment_status": status,
            "salary": round(fake.random_int(min=35000, max=180000, step=5000), -3),
            "manager_id": f"emp-{fake.random_int(min=1000, max=1000 + min(i, 50))}" if i > 10 else None
        })
    return employees

def main():
    source_name = os.environ.get("SOURCE_NAME", "hr")
    output_path = os.environ.get("OUTPUT_PATH", "./output")
    employee_count = int(os.environ.get("HR_EMPLOYEE_COUNT", "500"))

    os.makedirs(output_path, exist_ok=True)

    print(f"Generating {employee_count} employee records...")
    employees = generate_employees(employee_count)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_path, f"{source_name}_{timestamp}.json")

    with open(output_file, "w") as f:
        json.dump({
            "source": source_name,
            "extracted_at": datetime.utcnow().isoformat(),
            "record_count": len(employees),
            "records": employees
        }, f, indent=2)

    print(f"SUCCESS: Wrote {len(employees)} employees to {output_file}")
    sys.exit(0)

if __name__ == "__main__":
    main()
