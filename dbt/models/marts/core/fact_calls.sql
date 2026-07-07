with calls as (
    select * from {{ ref('stg_calls') }}
),

dim_date as (
    select * from {{ ref('dim_date') }}
),

dim_region as (
    select * from {{ ref('dim_region') }}
),

final as (
    select
        row_number() over (order by c.call_id) as call_key,
        dd.date_key,
        coalesce(dr.region_key, -1) as region_key,
        c.call_id,
        c.call_start_time,
        c.call_end_time,
        c.wait_time_seconds,
        c.call_duration_seconds,
        c.call_type,
        c.topic,
        c.disposition,
        c.is_resolved,
        c.agent_id,
        c.satisfaction_score
    from calls c
    left join dim_date dd 
        on dd.full_date = cast(c.call_start_time as date)
    left join dim_region dr
        on dr.region_name = 
            case
                when c.region = 'US-East' then 'US East'
                when c.region = 'US-West' then 'US West'
                when c.region = 'US-Central' then 'US Central'
                when c.region = 'UK-South' then 'UK South'
                when c.region = 'APAC-India' then 'India'
                when c.region = 'APAC-UAE' then 'UAE'
                else c.region
            end
)

select * from final
