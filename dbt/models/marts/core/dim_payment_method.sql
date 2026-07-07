with methods as (
    select 1 as payment_method_key, 'insurance' as payment_method union all
    select 2, 'self_pay' union all
    select 3, 'medicaid' union all
    select 4, 'medicare' union all
    select 5, 'no_charge'
)

select * from methods
