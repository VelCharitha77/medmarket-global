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

final as (
    select
        row_number() over (order by e.encounter_id) as booking_id,
        dd.date_key,
        coalesce(dp.provider_key, -1) as provider_key,
        coalesce(pat.patient_key, -1) as patient_key,
        coalesce(dr.region_key, -1) as region_key,
        e.encounter_id,
        e.encounter_start,
        e.encounter_end,
        e.encounter_class,
        e.description,
        e.base_cost,
        e.total_claim_cost,
        e.payer_coverage,
        e.reason_code,
        e.reason_description,
        case
            when e.encounter_end is null then 'no_show'
            else 'completed'
        end as status
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
)

select * from final
