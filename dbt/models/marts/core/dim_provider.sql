with providers as (
    select * from {{ ref('stg_providers') }}
),

final as (
    select
        row_number() over (order by npi) as provider_key,
        npi,
        first_name,
        last_name,
        first_name || ' ' || last_name as full_name,
        credential,
        gender,
        specialty,
        taxonomy_code,
        license_number,
        license_issue_date,
        license_expiration_date,
        case
            when license_expiration_date < current_date then 'expired'
            when license_expiration_date < current_date + interval '30 days' then 'expiring_soon'
            else 'valid'
        end as license_status,
        license_state,
        practice_city,
        practice_state,
        practice_zip,
        enumeration_date,
        status,
        true as is_current,
        current_date as effective_date,
        null::date as end_date
    from providers
)

select * from final
