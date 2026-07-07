-- This model contains Protected Health Information (PHI).
-- Access is restricted to the phi_restricted schema.
-- Only compliance and engineering roles may query this table.

with patients as (
    select * from {{ ref('dim_patient') }}
)

select
    patient_key,
    patient_id,
    first_name,
    last_name,
    first_name || ' ' || last_name as full_name,
    gender,
    birth_date,
    death_date,
    vital_status,
    age,
    marital_status,
    race,
    ethnicity,
    city,
    state,
    zip
from patients
