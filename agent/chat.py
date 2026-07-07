import os
#import json
import psycopg2
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Database connection — uses the analyst role (reporting_open only)
DB_URL = os.environ.get(
    "AGENT_DATABASE_URL",
    "postgresql://analyst:analyst_pass@localhost:5432/medmarket"
)

# Tables the agent is allowed to query — reporting_open schema only
ALLOWED_TABLES = [
    "reporting_open.reporting_patients",
    "public.fact_bookings",
    "public.fact_payments",
    "public.fact_calls",
    "public.dim_date",
    "public.dim_provider",
    "public.dim_region",
    "public.dim_payment_method",
    "public.mv_revenue_by_region_month",
    "public.mv_bookings_by_day_of_week",
]

# Schema context the agent needs to write correct SQL
SCHEMA_CONTEXT = """
Available tables and their columns:

reporting_open.reporting_patients:
  patient_key (int), patient_hash (text), gender (text), age_band (text), 
  vital_status (text), region_state (text)

public.fact_bookings:
  booking_id (int), date_key (int), provider_key (int), patient_key (int),
  region_key (int), encounter_id (text), encounter_start (timestamp),
  encounter_end (timestamp), encounter_class (text), description (text),
  base_cost (float), total_claim_cost (float), payer_coverage (float),
  reason_code (text), reason_description (text), status (text)

public.fact_payments:
  payment_id (int), date_key (int), provider_key (int), patient_key (int),
  region_key (int), payment_method_key (int), encounter_id (text),
  amount (float), base_cost (float), payer_coverage (float),
  patient_responsibility (float)

public.fact_calls:
  call_key (int), date_key (int), region_key (int), call_id (text),
  call_start_time (timestamp), call_end_time (timestamp),
  wait_time_seconds (int), call_duration_seconds (int), call_type (text),
  topic (text), disposition (text), is_resolved (boolean), agent_id (text),
  satisfaction_score (int)

public.dim_date:
  date_key (int), full_date (date), year (int), quarter (int),
  month_number (int), month_name (text), week_number (int),
  day_of_month (int), day_of_week_number (int), day_of_week_name (text),
  is_weekend (boolean), fiscal_quarter (text)

public.dim_provider:
  provider_key (int), npi (text), first_name (text), last_name (text),
  full_name (text), credential (text), gender (text), specialty (text),
  license_number (text), license_issue_date (date),
  license_expiration_date (date), license_status (text),
  practice_city (text), practice_state (text), practice_zip (text),
  status (text), is_current (boolean)

public.dim_region:
  region_key (int), region_code (text), region_name (text),
  country (text), currency_code (text), timezone (text),
  locale (text), rate_to_usd (float)

public.dim_payment_method:
  payment_method_key (int), payment_method (text)

public.mv_revenue_by_region_month:
  region_name (text), year (int), month_name (text), month_number (int),
  total_revenue (float), payment_count (int)

public.mv_bookings_by_day_of_week:
  day_of_week_name (text), day_of_week_number (int), booking_count (int),
  avg_claim_cost (numeric)

IMPORTANT RULES:
- NEVER query phi_restricted schema or any table not listed above
- NEVER use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or TRUNCATE
- Only use SELECT statements
- Always limit results to 50 rows maximum unless the user asks for more
- Use the materialized views (mv_*) when they match what's being asked
- Join fact tables to dimensions using the _key columns
- For patient data, only use reporting_open.reporting_patients (de-identified)
"""

SYSTEM_PROMPT = f"""You are a data analyst assistant for MedMarket Global, a healthcare marketplace platform.
You help users answer business questions by writing and explaining SQL queries against the data warehouse.

{SCHEMA_CONTEXT}

When the user asks a question:
1. Write a SQL query that answers it using ONLY the allowed tables listed above
2. Return ONLY the raw SQL query, nothing else — no markdown, no explanation, no backticks
3. If the question cannot be answered with the available tables, say "CANNOT_ANSWER:" followed by why

Remember: you are connected as a read-only analyst. You can only SELECT from the tables listed above."""


def validate_sql(sql):
    """Check that the generated SQL is safe to execute."""
    sql_upper = sql.upper().strip()
    
    # Block any non-SELECT statement
    dangerous_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "GRANT", "REVOKE"]
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            # Make sure it's a standalone keyword, not part of a column name
            import re
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                return False, f"Blocked: query contains '{keyword}'"
    
    if not sql_upper.startswith("SELECT"):
        return False, "Blocked: query must start with SELECT"
    
    # Check for phi_restricted references
    if "PHI_RESTRICTED" in sql_upper:
        return False, "Blocked: query references phi_restricted schema"
    
    return True, "OK"


def execute_query(sql):
    """Execute a validated SQL query and return results."""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    try:
        cur.execute(sql)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        return columns, rows, None
    except Exception as e:
        return None, None, str(e)
    finally:
        cur.close()
        conn.close()


def format_results(columns, rows, max_col_width=30):
    """Format query results as a readable table."""
    if not rows:
        return "No results returned."
    
    # Truncate values for display
    str_rows = []
    for row in rows:
        str_row = []
        for val in row:
            s = str(val) if val is not None else "NULL"
            if len(s) > max_col_width:
                s = s[:max_col_width-3] + "..."
            str_row.append(s)
        str_rows.append(str_row)
    
    # Calculate column widths
    widths = [len(c) for c in columns]
    for row in str_rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))
    
    # Build table
    header = " | ".join(c.ljust(w) for c, w in zip(columns, widths))
    separator = "-+-".join("-" * w for w in widths)
    lines = [header, separator]
    for row in str_rows:
        lines.append(" | ".join(val.ljust(w) for val, w in zip(row, widths)))
    
    return "\n".join(lines)


def summarize_results(client, question, sql, columns, rows):
    """Ask Claude to summarize the query results in plain English."""
    # Limit rows sent to Claude for summarization
    display_rows = rows[:20]
    results_text = format_results(columns, display_rows)
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""The user asked: "{question}"

This SQL query was run:
{sql}

Results ({len(rows)} total rows, showing first {len(display_rows)}):
{results_text}

Provide a brief, clear summary of what these results show. Be specific with numbers. 
Keep it to 2-3 sentences. If there are notable patterns or outliers, mention them."""
        }]
    )
    
    return response.content[0].text


def chat():
    """Main interactive chat loop."""
    client = anthropic.Anthropic()
    
    print("\n" + "=" * 60)
    print("  MedMarket Global — Data Warehouse Agent")
    print("  Ask questions in plain English about your data.")
    print("  Type 'quit' to exit.")
    print("=" * 60 + "\n")
    
    while True:
        question = input("You: ").strip()
        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        
        # Step 1: Generate SQL
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": question}]
            )
            sql = response.content[0].text.strip()
        except Exception as e:
            print(f"\nError generating SQL: {e}\n")
            continue
        
        # Check if agent said it can't answer
        if sql.startswith("CANNOT_ANSWER:"):
            print(f"\n{sql}\n")
            continue
        
        # Step 2: Validate SQL
        is_safe, reason = validate_sql(sql)
        if not is_safe:
            print(f"\nSafety check failed: {reason}")
            print(f"Generated SQL was: {sql}\n")
            continue
        
        print(f"\nSQL: {sql}\n")
        
        # Step 3: Execute query
        columns, rows, error = execute_query(sql)
        if error:
            print(f"Query error: {error}\n")
            continue
        
        # Step 4: Display results
        print(format_results(columns, rows[:20]))
        if len(rows) > 20:
            print(f"\n... ({len(rows)} total rows, showing first 20)")
        
        # Step 5: Summarize
        try:
            summary = summarize_results(client, question, sql, columns, rows)
            print(f"\nSummary: {summary}\n")
        except Exception as e:
            print(f"\n(Could not generate summary: {e})\n")


if __name__ == "__main__":
    chat()