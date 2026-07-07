with source as (
    select * from {{ source('raw', 'raw_calls') }}
),

cleaned as (
    select
        call_id,
        cast(call_start_time as timestamp) as call_start_time,
        cast(call_end_time as timestamp) as call_end_time,
        wait_time_seconds,
        call_duration_seconds,
        trim(region) as region,
        trim(call_type) as call_type,
        trim(topic) as topic,
        trim(disposition) as disposition,
        is_resolved,
        agent_id,
        satisfaction_score
    from source
    where call_id is not null
)

select * from cleaned
