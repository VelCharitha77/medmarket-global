with source as (
    select * from {{ source('raw', 'raw_employees') }}
),

cleaned as (
    select
        employee_id,
        trim(first_name) as first_name,
        trim(last_name) as last_name,
        trim(email) as email,
        trim(department) as department,
        trim(job_title) as job_title,
        trim(region) as region,
        cast(hire_date as date) as hire_date,
        cast(nullif(termination_date, '') as date) as termination_date,
        trim(employment_status) as employment_status,
        salary,
        manager_id
    from source
    where employee_id is not null
)

select * from cleaned
