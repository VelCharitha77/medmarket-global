with source as (
    select * from {{ source('raw', 'raw_crm_contacts') }}
),

cleaned as (
    select
        contact_id,
        trim(email) as email,
        trim(first_name) as first_name,
        trim(last_name) as last_name,
        trim(company) as company,
        trim(phone) as phone,
        trim(lifecycle_stage) as lifecycle_stage,
        trim(lead_source) as lead_source,
        trim(region) as region,
        cast(created_at as timestamp) as created_at,
        cast(last_activity_date as timestamp) as last_activity_date,
        is_active
    from source
    where contact_id is not null
)

select * from cleaned
