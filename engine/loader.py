"""
Loads the most recent raw JSON output from each connector into
raw tables in the Postgres warehouse.
"""
import os
import json
import glob
import psycopg2
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("engine.loader")

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:devpass123@localhost:5432/medmarket"
)
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "output")

def get_latest_file(prefix):
    """Find the most recent output file matching a prefix."""
    pattern = os.path.join(OUTPUT_DIR, f"{prefix}*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matching {pattern}")
    return files[-1]

def load_json(filepath):
    """Read and parse a JSON output file."""
    with open(filepath, "r") as f:
        data = json.load(f)
    logger.info(f"Loaded {data['record_count']} records from {filepath}")
    return data["records"]

def create_raw_tables(cur):
    """Create raw landing tables if they don't exist."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_providers (
            npi TEXT,
            first_name TEXT,
            last_name TEXT,
            credential TEXT,
            gender TEXT,
            specialty TEXT,
            taxonomy_code TEXT,
            license_number TEXT,
            license_issue_date TEXT,
            license_expiration_date TEXT,
            state TEXT,
            practice_city TEXT,
            practice_state TEXT,
            practice_zip TEXT,
            enumeration_date TEXT,
            last_updated TEXT,
            status TEXT,
            loaded_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS raw_patients (
            id TEXT,
            birthdate TEXT,
            deathdate TEXT,
            ssn TEXT,
            prefix TEXT,
            first_name TEXT,
            last_name TEXT,
            marital TEXT,
            race TEXT,
            ethnicity TEXT,
            gender TEXT,
            birthplace TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            county TEXT,
            zip TEXT,
            lat TEXT,
            lon TEXT,
            healthcare_expenses TEXT,
            healthcare_coverage TEXT,
            income TEXT,
            loaded_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS raw_encounters (
            id TEXT,
            start_time TEXT,
            stop_time TEXT,
            patient TEXT,
            organization TEXT,
            provider TEXT,
            payer TEXT,
            encounterclass TEXT,
            code TEXT,
            description TEXT,
            base_encounter_cost TEXT,
            total_claim_cost TEXT,
            payer_coverage TEXT,
            reasoncode TEXT,
            reasondescription TEXT,
            loaded_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS raw_crm_contacts (
            contact_id TEXT,
            email TEXT,
            first_name TEXT,
            last_name TEXT,
            company TEXT,
            phone TEXT,
            lifecycle_stage TEXT,
            lead_source TEXT,
            region TEXT,
            created_at TEXT,
            last_activity_date TEXT,
            is_active BOOLEAN,
            loaded_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS raw_employees (
            employee_id TEXT,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            department TEXT,
            job_title TEXT,
            region TEXT,
            hire_date TEXT,
            termination_date TEXT,
            employment_status TEXT,
            salary INTEGER,
            manager_id TEXT,
            loaded_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS raw_calls (
            call_id TEXT,
            call_start_time TEXT,
            call_end_time TEXT,
            wait_time_seconds INTEGER,
            call_duration_seconds INTEGER,
            region TEXT,
            call_type TEXT,
            topic TEXT,
            disposition TEXT,
            is_resolved BOOLEAN,
            agent_id TEXT,
            customer_phone TEXT,
            satisfaction_score INTEGER,
            loaded_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS raw_regions (
            region_code TEXT,
            region_name TEXT,
            country TEXT,
            currency_code TEXT,
            timezone TEXT,
            locale TEXT,
            loaded_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS raw_fx_rates (
            currency_code TEXT,
            rate_to_usd FLOAT,
            rate_date TEXT,
            loaded_at TIMESTAMP DEFAULT NOW()
        );
    """)

def insert_records(cur, table_name, records, columns):
    """Insert a list of records into a table, replacing existing data."""
    cur.execute(f"DELETE FROM {table_name}")
    logger.info(f"Cleared {table_name}")

    if not records:
        return

    placeholders = ", ".join(["%s"] * len(columns))
    col_names = ", ".join(columns)
    sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"

    for record in records:
        values = [record.get(col) for col in columns]
        cur.execute(sql, values)

    logger.info(f"Inserted {len(records)} records into {table_name}")

def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    create_raw_tables(cur)
    conn.commit()

    # Load each source
    try:
        # NPI providers
        records = load_json(get_latest_file("npi_registry_"))
        insert_records(cur, "raw_providers", records, [
            "npi", "first_name", "last_name", "credential", "gender",
            "specialty", "taxonomy_code", "license_number",
            "license_issue_date", "license_expiration_date",
            "state", "practice_city", "practice_state", "practice_zip",
            "enumeration_date", "last_updated", "status"
        ])

        # EHR patients
        records = load_json(get_latest_file("ehr_patients_"))
        patient_col_map = {
            "Id": "id", "BIRTHDATE": "birthdate", "DEATHDATE": "deathdate",
            "SSN": "ssn", "PREFIX": "prefix", "FIRST": "first_name",
            "LAST": "last_name", "MARITAL": "marital", "RACE": "race",
            "ETHNICITY": "ethnicity", "GENDER": "gender", "BIRTHPLACE": "birthplace",
            "ADDRESS": "address", "CITY": "city", "STATE": "state",
            "COUNTY": "county", "ZIP": "zip", "LAT": "lat", "LON": "lon",
            "HEALTHCARE_EXPENSES": "healthcare_expenses",
            "HEALTHCARE_COVERAGE": "healthcare_coverage", "INCOME": "income"
        }
        mapped_records = []
        for r in records:
            mapped = {v: r.get(k, "") for k, v in patient_col_map.items()}
            mapped_records.append(mapped)
        insert_records(cur, "raw_patients", mapped_records, list(patient_col_map.values()))

        # EHR encounters
        records = load_json(get_latest_file("ehr_encounters_"))
        encounter_col_map = {
            "Id": "id", "START": "start_time", "STOP": "stop_time",
            "PATIENT": "patient", "ORGANIZATION": "organization",
            "PROVIDER": "provider", "PAYER": "payer",
            "ENCOUNTERCLASS": "encounterclass", "CODE": "code",
            "DESCRIPTION": "description", "BASE_ENCOUNTER_COST": "base_encounter_cost",
            "TOTAL_CLAIM_COST": "total_claim_cost", "PAYER_COVERAGE": "payer_coverage",
            "REASONCODE": "reasoncode", "REASONDESCRIPTION": "reasondescription"
        }
        mapped_records = []
        for r in records:
            mapped = {v: r.get(k, "") for k, v in encounter_col_map.items()}
            mapped_records.append(mapped)
        insert_records(cur, "raw_encounters", mapped_records, list(encounter_col_map.values()))

        # CRM contacts
        records = load_json(get_latest_file("hubspot_crm_"))
        insert_records(cur, "raw_crm_contacts", records, [
            "contact_id", "email", "first_name", "last_name", "company",
            "phone", "lifecycle_stage", "lead_source", "region",
            "created_at", "last_activity_date", "is_active"
        ])

        # HR employees
        records = load_json(get_latest_file("hr_"))
        insert_records(cur, "raw_employees", records, [
            "employee_id", "first_name", "last_name", "email",
            "department", "job_title", "region", "hire_date",
            "termination_date", "employment_status", "salary", "manager_id"
        ])

        # Call center
        records = load_json(get_latest_file("call_center_"))
        insert_records(cur, "raw_calls", records, [
            "call_id", "call_start_time", "call_end_time",
            "wait_time_seconds", "call_duration_seconds", "region",
            "call_type", "topic", "disposition", "is_resolved",
            "agent_id", "customer_phone", "satisfaction_score"
        ])

        # Regions
        records = load_json(get_latest_file("region_fx_regions_"))
        insert_records(cur, "raw_regions", records, [
            "region_code", "region_name", "country", "currency_code", "timezone", "locale"
        ])

        # FX rates
        records = load_json(get_latest_file("region_fx_fx_rates_"))
        insert_records(cur, "raw_fx_rates", records, [
            "currency_code", "rate_to_usd", "rate_date"
        ])

        conn.commit()
        logger.info("All raw data loaded successfully")

    except Exception as e:
        conn.rollback()
        logger.error(f"Load failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
