with source as (
    select * from {{ source('raw', 'raw_providers') }}
),

cleaned as (
    select
        npi,
        trim(upper(first_name)) as first_name,
        trim(upper(last_name)) as last_name,
        trim(credential) as credential,
        case 
            when upper(gender) = 'M' then 'Male'
            when upper(gender) = 'F' then 'Female'
            else 'Unknown'
        end as gender,
        trim(specialty) as specialty,
        taxonomy_code,
        license_number,
        cast(license_issue_date as date) as license_issue_date,
        cast(license_expiration_date as date) as license_expiration_date,
        upper(trim(state)) as license_state,
        upper(trim(practice_city)) as practice_city,
        upper(trim(practice_state)) as practice_state,
        trim(practice_zip) as practice_zip,
        cast(enumeration_date as date) as enumeration_date,
        cast(last_updated as date) as last_updated,
        case 
            when upper(status) = 'A' then 'active'
            else 'inactive'
        end as status,
        row_number() over (partition by npi order by last_updated desc) as rn
    from source
    where npi is not null
)

select
    npi, first_name, last_name, credential, gender, specialty,
    taxonomy_code, license_number, license_issue_date, license_expiration_date,
    license_state, practice_city, practice_state, practice_zip,
    enumeration_date, last_updated, status
from cleaned
where rn = 1
