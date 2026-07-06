# MedMarket Global — Data Model (Phase 1 Deliverable)

## Business questions this model answers

1. Total revenue by region, by month
2. Provider utilization and no-show rate
3. Call center performance (volume, wait times, resolution rate) by region
4. Which providers have licenses expiring soon (answered via `dim_provider` attribute, not a fact table)
5. Scheduling volume trends (answered via `fact_bookings`, grouped by date instead of provider)

## Fact tables

### fact_bookings
**Grain:** One row per currently-scheduled appointment. A reschedule updates the existing row in place — it does not create a new row. No transfer/callback-style complexity modeled.

| Column | Type | Description |
|---|---|---|
| booking_id | surrogate key | Unique row identifier |
| date_key | FK → dim_date | Date of the appointment |
| region_id | FK → dim_region | Region/marketplace the booking occurred in |
| provider_id | FK → dim_provider | Provider seeing the patient |
| patient_key | FK → dim_patient | De-identified patient reference |
| status | text | scheduled / completed / no_show / cancelled |

### fact_payments
**Grain:** One row per payment made for a single appointment. No installment/multi-appointment invoice support modeled.

| Column | Type | Description |
|---|---|---|
| payment_id | surrogate key | Unique row identifier |
| date_key | FK → dim_date | Date the payment occurred |
| region_id | FK → dim_region | Region the payment occurred in |
| provider_id | FK → dim_provider | Provider associated with the appointment paid for |
| patient_key | FK → dim_patient | De-identified patient reference |
| payment_method_id | FK → dim_payment_method | How the payment was made |
| amount | numeric | Payment amount |

### fact_calls
**Grain:** One row per call handled by the call center. No transfer/multi-leg call complexity modeled.

| Column | Type | Description |
|---|---|---|
| call_id | surrogate key | Unique row identifier |
| date_key | FK → dim_date | Date of the call |
| region_id | FK → dim_region | Region the call was routed to/from |
| wait_time_seconds | numeric | Time caller spent waiting |
| call_duration_seconds | numeric | Total call length |
| is_resolved | boolean | Whether the call was resolved on first contact |

## Dimension tables

### dim_date (conformed — shared across all facts)
One row per calendar day. SCD: Type 0 (never changes).
| Column | Description |
|---|---|
| date_key | Surrogate key (e.g., 20260710) |
| full_date | Actual date |
| day_of_week, month_name, quarter, year, is_weekend | Pre-computed convenience columns |

### dim_region (conformed — shared across all facts)
SCD: Type 1 (overwrite — no historical need for currency/timezone changes).
| Column | Description |
|---|---|
| region_id | Surrogate key |
| region_name, country, currency_code, timezone | Descriptive attributes |

### dim_provider
SCD policy — mixed, per attribute:
| Attribute | SCD Type | Reasoning |
|---|---|---|
| name | Type 1 | No historical need (typo fixes only) |
| specialty | **Type 2** | Historical bookings must reflect specialty at time of booking |
| license_status | **Type 2** | Compliance/audit accuracy — a booking's provider status must not change retroactively |
| license_expiration_date | Type 1 | Current-state attribute, answers the credentialing business question directly |

Type 2 columns required: `effective_date`, `end_date`, `is_current`.

### dim_patient (lives in `phi_restricted` schema; de-identified copy in `reporting_open`)
SCD: Type 1 for now (region/demographic changes, no strong historical need identified yet).

### dim_payment_method
Small static reference table (credit card, insurance, cash, etc.). SCD: Type 1.

## Source-to-model mapping (to be completed during Phase 4 connector build)

| Target column | Source system | Source field | Transformation |
|---|---|---|---|
| fact_bookings.provider_id | NextGen (synthetic via Synthea) | Encounter.provider | Lookup to dim_provider surrogate key |
| fact_bookings.patient_key | NextGen | Patient.id | Tokenized/hashed before entering reporting_open |
| dim_provider.specialty | NPI Registry API | taxonomies[].desc | Direct copy, feeds Type 2 snapshot logic |
| dim_provider.license_expiration_date | Modio stand-in (synthetic) | N/A — generated via Faker | Synthetic, since NPI doesn't expose this |
| fact_calls.wait_time_seconds | Five9 stand-in | call.wait_time | Direct copy |
| fact_payments.amount | Billing system (synthetic) | payment.amount | Currency conversion via dim_fx_rate if cross-region rollup needed |

*(This table will be filled in fully once each connector in Phase 4 is built — it's intentionally a skeleton for now.)*

## Explicit assumptions made during this design

- A reschedule updates the existing booking row rather than creating a new one (no reschedule-history tracking in v1)
- A payment always maps to exactly one appointment (no installments/invoices in v1)
- A call is a single, self-contained interaction (no transfer/multi-leg modeling in v1)
- `dim_agent` was deliberately not built — no business question currently requires it
