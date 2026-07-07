-- De-identified patient data safe for general reporting.
-- No names, exact birth dates, addresses, or other direct identifiers.
-- Only age_band, gender, and a hashed patient key remain.

with patients as (
    select * from {{ ref('dim_patient') }}
)

select
    patient_key,
    md5(patient_id::text || 'medmarket_salt_2026') as patient_hash,
    gender,
    age_band,
    vital_status,
    state as region_state
from patients
