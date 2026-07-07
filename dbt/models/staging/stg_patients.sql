with source as (
    select * from {{ source('raw', 'raw_patients') }}
),

cleaned as (
    select
        id as patient_id,
        cast(birthdate as date) as birth_date,
        cast(nullif(deathdate, '') as date) as death_date,
        trim(prefix) as prefix,
        trim(first_name) as first_name,
        trim(last_name) as last_name,
        trim(marital) as marital_status,
        trim(race) as race,
        trim(ethnicity) as ethnicity,
        case
            when upper(gender) = 'M' then 'Male'
            when upper(gender) = 'F' then 'Female'
            else 'Unknown'
        end as gender,
        trim(city) as city,
        trim(state) as state,
        trim(county) as county,
        trim(zip) as zip,
        cast(lat as float) as latitude,
        cast(lon as float) as longitude,
        cast(healthcare_expenses as float) as healthcare_expenses,
        cast(healthcare_coverage as float) as healthcare_coverage,
        cast(income as float) as income
    from source
    where id is not null
)

select * from cleaned
