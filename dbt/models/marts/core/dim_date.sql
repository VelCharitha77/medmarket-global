with date_spine as (
    select
        generate_series(
            '1930-01-01'::date,
            '2030-12-31'::date,
            '1 day'::interval
        )::date as full_date
),

enriched as (
    select
        to_char(full_date, 'YYYYMMDD')::int as date_key,
        full_date,
        extract(year from full_date)::int as year,
        extract(quarter from full_date)::int as quarter,
        extract(month from full_date)::int as month_number,
        to_char(full_date, 'Month') as month_name,
        extract(week from full_date)::int as week_number,
        extract(day from full_date)::int as day_of_month,
        extract(dow from full_date)::int as day_of_week_number,
        to_char(full_date, 'Day') as day_of_week_name,
        case when extract(dow from full_date) in (0, 6) then true else false end as is_weekend,
        'Q' || extract(quarter from full_date)::text || ' ' || extract(year from full_date)::text as fiscal_quarter
    from date_spine
)

select * from enriched
