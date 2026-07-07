import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="MedMarket Global — Pipeline Monitor",
    page_icon="🏥",
    layout="wide"
)

# Database connection
DB_URL = "postgresql://postgres:devpass123@localhost:5432/medmarket"

@st.cache_data(ttl=60)
def run_query(sql):
    """Run a SQL query and return results as a DataFrame."""
    try:
        conn = psycopg2.connect(DB_URL)
        df = pd.read_sql(sql, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()


# ============================================================
# SIDEBAR — Navigation
# ============================================================
st.sidebar.title("MedMarket Global")
page = st.sidebar.radio("Navigate", [
    "Pipeline Health",
    "Revenue",
    "Call Center",
    "Credentialing",
    "Scheduling"
])


# ============================================================
# PAGE 1: Pipeline Health
# ============================================================
if page == "Pipeline Health":
    st.title("Pipeline Health Monitor")

    # Recent job runs
    st.subheader("Recent Job Runs")
    df_runs = run_query("""
        SELECT dag_name, job_name, status, start_time, 
               duration_seconds, error
        FROM job_runs 
        ORDER BY created_at DESC 
        LIMIT 30
    """)

    if not df_runs.empty:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        total = len(df_runs)
        succeeded = len(df_runs[df_runs["status"] == "success"])
        failed = len(df_runs[df_runs["status"] == "failed"])
        skipped = len(df_runs[df_runs["status"] == "skipped"])

        col1.metric("Total Runs", total)
        col2.metric("Succeeded", succeeded, delta=None)
        col3.metric("Failed", failed, delta=None)
        col4.metric("Skipped", skipped, delta=None)

        # Success rate gauge
        success_rate = round(succeeded / total * 100, 1) if total > 0 else 0
        st.metric("Overall Success Rate", f"{success_rate}%")

        # Status breakdown chart
        status_counts = df_runs["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        color_map = {"success": "#2ecc71", "failed": "#e74c3c", "skipped": "#f39c12"}
        fig = px.pie(status_counts, values="count", names="status",
                     color="status", color_discrete_map=color_map,
                     title="Job Status Distribution")
        st.plotly_chart(fig, use_container_width=True)

        # Duration trend
        df_duration = df_runs[df_runs["duration_seconds"].notna()].copy()
        if not df_duration.empty:
            fig2 = px.bar(df_duration, x="job_name", y="duration_seconds",
                         color="status", color_discrete_map=color_map,
                         title="Job Duration (seconds)")
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)

        # Recent failures
        df_failures = df_runs[df_runs["status"] == "failed"]
        if not df_failures.empty:
            st.subheader("Recent Failures")
            st.dataframe(df_failures[["dag_name", "job_name", "start_time", "error"]], 
                        use_container_width=True)
        else:
            st.success("No recent failures!")

        # Full run table
        st.subheader("Full Run History")
        st.dataframe(df_runs, use_container_width=True)
    else:
        st.warning("No job runs found. Run the pipeline first.")


# ============================================================
# PAGE 2: Revenue
# ============================================================
elif page == "Revenue":
    st.title("Revenue by Region")

    df_revenue = run_query("""
        SELECT region_name, year, month_name, month_number,
               total_revenue, payment_count
        FROM mv_revenue_by_region_month
        ORDER BY year, month_number
    """)

    if not df_revenue.empty:
        # Summary metrics
        total_revenue = df_revenue["total_revenue"].sum()
        total_payments = df_revenue["payment_count"].sum()
        avg_per_payment = total_revenue / total_payments if total_payments > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Revenue", f"${total_revenue:,.0f}")
        col2.metric("Total Payments", f"{total_payments:,}")
        col3.metric("Avg per Payment", f"${avg_per_payment:,.2f}")

        # Revenue by region (bar chart)
        df_by_region = df_revenue.groupby("region_name").agg(
            total_revenue=("total_revenue", "sum"),
            payment_count=("payment_count", "sum")
        ).reset_index().sort_values("total_revenue", ascending=False)

        fig = px.bar(df_by_region, x="region_name", y="total_revenue",
                    title="Total Revenue by Region",
                    labels={"total_revenue": "Revenue ($)", "region_name": "Region"},
                    color="total_revenue", color_continuous_scale="blues")
        st.plotly_chart(fig, use_container_width=True)

        # Revenue over time (line chart)
        df_revenue["period"] = df_revenue["year"].astype(str) + "-" + df_revenue["month_number"].astype(str).str.zfill(2)
        fig2 = px.line(df_revenue, x="period", y="total_revenue",
                      color="region_name",
                      title="Revenue Trend Over Time",
                      labels={"total_revenue": "Revenue ($)", "period": "Period"})
        st.plotly_chart(fig2, use_container_width=True)

        # Data table
        st.subheader("Revenue Detail")
        st.dataframe(df_revenue, use_container_width=True)
    else:
        st.warning("No revenue data found.")


# ============================================================
# PAGE 3: Call Center
# ============================================================
elif page == "Call Center":
    st.title("Call Center Performance")

    df_calls = run_query("""
        SELECT r.region_name,
               COUNT(*) as total_calls,
               ROUND(AVG(c.wait_time_seconds)::numeric, 1) as avg_wait_seconds,
               ROUND(AVG(c.call_duration_seconds)::numeric, 1) as avg_duration_seconds,
               SUM(CASE WHEN c.is_resolved THEN 1 ELSE 0 END) as resolved_count,
               ROUND(SUM(CASE WHEN c.is_resolved THEN 1 ELSE 0 END) * 100.0 / COUNT(*)::numeric, 1) as resolution_rate
        FROM fact_calls c
        JOIN dim_region r ON c.region_key = r.region_key
        GROUP BY r.region_name
        ORDER BY total_calls DESC
    """)

    if not df_calls.empty:
        # Summary metrics
        total_calls = df_calls["total_calls"].sum()
        avg_wait = df_calls["avg_wait_seconds"].mean()
        overall_resolution = df_calls["resolved_count"].sum() / total_calls * 100 if total_calls > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Calls", f"{total_calls:,}")
        col2.metric("Avg Wait Time", f"{avg_wait:.0f}s")
        col3.metric("Resolution Rate", f"{overall_resolution:.1f}%")

        # Resolution rate by region
        fig = px.bar(df_calls, x="region_name", y="resolution_rate",
                    title="Resolution Rate by Region (%)",
                    labels={"resolution_rate": "Resolution Rate (%)", "region_name": "Region"},
                    color="resolution_rate", color_continuous_scale="greens")
        st.plotly_chart(fig, use_container_width=True)

        # Wait time by region
        fig2 = px.bar(df_calls, x="region_name", y="avg_wait_seconds",
                     title="Average Wait Time by Region (seconds)",
                     labels={"avg_wait_seconds": "Avg Wait (s)", "region_name": "Region"},
                     color="avg_wait_seconds", color_continuous_scale="reds")
        st.plotly_chart(fig2, use_container_width=True)

        # Topic breakdown
        df_topics = run_query("""
            SELECT topic, COUNT(*) as call_count,
                   ROUND(SUM(CASE WHEN is_resolved THEN 1 ELSE 0 END) * 100.0 / COUNT(*)::numeric, 1) as resolution_rate
            FROM fact_calls
            GROUP BY topic
            ORDER BY call_count DESC
        """)
        if not df_topics.empty:
            st.subheader("Calls by Topic")
            fig3 = px.bar(df_topics, x="topic", y="call_count",
                         color="resolution_rate", color_continuous_scale="greens",
                         title="Call Volume by Topic (colored by resolution rate)",
                         labels={"call_count": "Calls", "topic": "Topic"})
            fig3.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig3, use_container_width=True)

        # Data table
        st.subheader("Call Center Detail")
        st.dataframe(df_calls, use_container_width=True)
    else:
        st.warning("No call data found.")


# ============================================================
# PAGE 4: Credentialing
# ============================================================
elif page == "Credentialing":
    st.title("Provider Credentialing Status")

    df_cred = run_query("""
        SELECT license_status, COUNT(*) as provider_count
        FROM dim_provider
        GROUP BY license_status
        ORDER BY provider_count DESC
    """)

    if not df_cred.empty:
        # Summary metrics
        total = df_cred["provider_count"].sum()
        expired = df_cred[df_cred["license_status"] == "expired"]["provider_count"].sum()
        expiring = df_cred[df_cred["license_status"] == "expiring_soon"]["provider_count"].sum()
        valid = df_cred[df_cred["license_status"] == "valid"]["provider_count"].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Providers", total)
        col2.metric("Valid", int(valid))
        col3.metric("Expiring Soon", int(expiring), delta=f"-{int(expiring)}" if expiring > 0 else None, delta_color="inverse")
        col4.metric("Expired", int(expired), delta=f"-{int(expired)}" if expired > 0 else None, delta_color="inverse")

        # Status pie chart
        color_map = {"valid": "#2ecc71", "expiring_soon": "#f39c12", "expired": "#e74c3c"}
        fig = px.pie(df_cred, values="provider_count", names="license_status",
                    color="license_status", color_discrete_map=color_map,
                    title="License Status Distribution")
        st.plotly_chart(fig, use_container_width=True)

        # Providers expiring soon — detail list
        df_expiring = run_query("""
            SELECT full_name, specialty, practice_state,
                   license_expiration_date, license_status
            FROM dim_provider
            WHERE license_status IN ('expired', 'expiring_soon')
            ORDER BY license_expiration_date
        """)
        if not df_expiring.empty:
            st.subheader("Providers Requiring Attention")
            st.dataframe(df_expiring, use_container_width=True)
        else:
            st.success("All provider licenses are current!")
    else:
        st.warning("No credentialing data found.")


# ============================================================
# PAGE 5: Scheduling
# ============================================================
elif page == "Scheduling":
    st.title("Scheduling & Booking Trends")

    # Bookings by day of week
    df_dow = run_query("""
        SELECT day_of_week_name, day_of_week_number, 
               booking_count, avg_claim_cost
        FROM mv_bookings_by_day_of_week
        ORDER BY day_of_week_number
    """)

    if not df_dow.empty:
        total_bookings = df_dow["booking_count"].sum()
        busiest_day = df_dow.loc[df_dow["booking_count"].idxmax(), "day_of_week_name"]
        avg_cost = df_dow["avg_claim_cost"].mean()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Bookings", f"{total_bookings:,}")
        col2.metric("Busiest Day", busiest_day.strip())
        col3.metric("Avg Claim Cost", f"${avg_cost:,.2f}")

        # Bookings by day of week bar chart
        fig = px.bar(df_dow, x="day_of_week_name", y="booking_count",
                    title="Bookings by Day of Week",
                    labels={"booking_count": "Bookings", "day_of_week_name": "Day"},
                    color="booking_count", color_continuous_scale="blues")
        st.plotly_chart(fig, use_container_width=True)

        # Avg claim cost by day
        fig2 = px.bar(df_dow, x="day_of_week_name", y="avg_claim_cost",
                     title="Average Claim Cost by Day of Week",
                     labels={"avg_claim_cost": "Avg Cost ($)", "day_of_week_name": "Day"},
                     color="avg_claim_cost", color_continuous_scale="oranges")
        st.plotly_chart(fig2, use_container_width=True)

    # Booking volume over time
    df_monthly = run_query("""
        SELECT d.year, d.month_number, d.month_name, COUNT(*) as bookings
        FROM fact_bookings b
        JOIN dim_date d ON b.date_key = d.date_key
        WHERE d.year >= 2020
        GROUP BY d.year, d.month_number, d.month_name
        ORDER BY d.year, d.month_number
    """)

    if not df_monthly.empty:
        df_monthly["period"] = df_monthly["year"].astype(str) + "-" + df_monthly["month_number"].astype(str).str.zfill(2)
        fig3 = px.line(df_monthly, x="period", y="bookings",
                      title="Monthly Booking Volume (2020+)",
                      labels={"bookings": "Bookings", "period": "Period"})
        st.plotly_chart(fig3, use_container_width=True)

    else:
        st.warning("No booking data found.")


# Footer
st.sidebar.markdown("---")
st.sidebar.caption("MedMarket Global Data Platform v1.0")
st.sidebar.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
