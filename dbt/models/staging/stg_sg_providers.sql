with source as (
    select * from {{ source('raw', 'raw_sg_providers') }}
),

cleaned as (
    select
        npi,
        trim(first_name) as first_name,
        trim(last_name) as last_name,
        trim(credential) as credential,
        gender,
        trim(specialty) as specialty,
        taxonomy_code,
        license_number,
        cast(license_issue_date as date) as license_issue_date,
        cast(license_expiration_date as date) as license_expiration_date,
        upper(trim(state)) as license_state,
        trim(practice_city) as practice_city,
        trim(practice_state) as practice_state,
        trim(practice_zip) as practice_zip,
        cast(enumeration_date as date) as enumeration_date,
        cast(last_updated as date) as last_updated,
        case
            when upper(status) = 'A' then 'active'
            else 'inactive'
        end as status
    from source
    where npi is not null
)

select * from cleaned
