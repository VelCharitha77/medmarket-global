with patients as (
    select * from {{ ref('stg_patients') }}
),

final as (
    select
        row_number() over (order by patient_id) as patient_key,
        patient_id,
        first_name,
        last_name,
        gender,
        birth_date,
        death_date,
        case
            when death_date is not null then 'deceased'
            else 'alive'
        end as vital_status,
        extract(year from age(
            coalesce(death_date, current_date),
            birth_date
        ))::int as age,
        case
            when extract(year from age(coalesce(death_date, current_date), birth_date)) < 18 then 'under_18'
            when extract(year from age(coalesce(death_date, current_date), birth_date)) < 65 then '18_64'
            else '65_plus'
        end as age_band,
        marital_status,
        race,
        ethnicity,
        city,
        state,
        zip
    from patients
)

select * from final
