with encounters as (
    select * from {{ ref('stg_encounters') }}
),

dim_date as (
    select * from {{ ref('dim_date') }}
),

dim_provider as (
    select * from {{ ref('dim_provider') }}
),

dim_patient as (
    select * from {{ ref('dim_patient') }}
),

dim_region as (
    select * from {{ ref('dim_region') }}
),

dim_payment_method as (
    select * from {{ ref('dim_payment_method') }}
),

final as (
    select
        row_number() over (order by e.encounter_id) as payment_id,
        dd.date_key,
        coalesce(dp.provider_key, -1) as provider_key,
        coalesce(pat.patient_key, -1) as patient_key,
        coalesce(dr.region_key, -1) as region_key,
        case
            when e.payer_coverage > 0 then 1
            else 2
        end as payment_method_key,
        e.encounter_id,
        e.total_claim_cost as amount,
        e.base_cost,
        e.payer_coverage,
        e.total_claim_cost - e.payer_coverage as patient_responsibility
    from encounters e
    left join dim_date dd 
        on dd.full_date = cast(e.encounter_start as date)
    left join dim_patient pat 
        on pat.patient_id = e.patient_id
    left join dim_provider dp 
        on dp.npi = e.provider_id
    left join dim_region dr 
        on dr.region_code = 
            case 
                when pat.state in ('Massachusetts', 'New York', 'Connecticut') then 'US-EAST'
                when pat.state in ('California', 'Oregon', 'Washington') then 'US-WEST'
                else 'US-CENTRAL'
            end
    where e.total_claim_cost > 0
)

select * from final
