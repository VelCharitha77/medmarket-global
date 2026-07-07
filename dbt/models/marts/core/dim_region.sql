with regions as (
    select * from {{ source('raw', 'raw_regions') }}
),

fx_rates as (
    select * from {{ source('raw', 'raw_fx_rates') }}
),

final as (
    select
        row_number() over (order by r.region_code) as region_key,
        r.region_code,
        r.region_name,
        r.country,
        r.currency_code,
        r.timezone,
        r.locale,
        coalesce(fx.rate_to_usd, 1.0) as rate_to_usd
    from regions r
    left join fx_rates fx on r.currency_code = fx.currency_code
)

select * from final
