with source as (
    select * from {{ source('raw', 'raw_encounters') }}
),

cleaned as (
    select
        id as encounter_id,
        cast(start_time as timestamp) as encounter_start,
        cast(stop_time as timestamp) as encounter_end,
        patient as patient_id,
        organization as organization_id,
        provider as provider_id,
        payer as payer_id,
        trim(encounterclass) as encounter_class,
        code as encounter_code,
        trim(description) as description,
        cast(base_encounter_cost as float) as base_cost,
        cast(total_claim_cost as float) as total_claim_cost,
        cast(payer_coverage as float) as payer_coverage,
        nullif(trim(reasoncode), '') as reason_code,
        nullif(trim(reasondescription), '') as reason_description
    from source
    where id is not null
)

select * from cleaned
