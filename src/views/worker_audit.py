from datetime import datetime, date
import pandas as pd
import streamlit as st

from src.db import (
    get_all_workers,
    get_worker_punches_history
)
from src.components import (
    render_page_header,
    style_attendance_df
)


def render_worker_audit_view() -> None:
    """Renders Tab 3: Individual worker profiles, punch timelines, and work history analytics."""
    render_page_header(
        title="Worker-Wise Audit & History",
        subtitle="Detailed shift history, total cumulative hours, and attendance logs per worker"
    )

    # 1. Fetch Registered Workers
    workers = get_all_workers(active_only=False)
    if not workers:
        st.warning("No worker profiles found in the system.")
        return

    # 2. Worker Selector Dropdown
    worker_options = {
        f"#{w['duty_number']} - {w['full_name']} ({w.get('department', 'General')})": w
        for w in workers
    }

    col_picker, _ = st.columns([2, 1])
    with col_picker:
        selected_label = st.selectbox(
            "Select Worker to Inspect:",
            options=list(worker_options.keys()),
            key="audit_worker_select"
        )
        selected_worker = worker_options[selected_label]
        duty_no = selected_worker["duty_number"]

    # 3. Retrieve Historical Punches from Supabase
    punches = get_worker_punches_history(duty_no)

    if not punches:
        st.info(f"No shift or punch records found for **{selected_worker['full_name']}** (#{duty_no}).")
        return

    # Convert punches to DataFrame for analytics
    df = pd.DataFrame(punches)

    # 4. Compute Cumulative Analytics
    total_shifts = len(df)
    
    # Clean hours column
    df["total_hours"] = pd.to_numeric(df["total_hours"], errors="coerce").fillna(0.0)
    total_hours_worked = df["total_hours"].sum()
    avg_hours_per_shift = (total_hours_worked / total_shifts) if total_shifts > 0 else 0.0

    # Remote vs On-Site Breakdown
    wfh_shifts = len(df[df["status"] == "WFH"])
    on_site_shifts = total_shifts - wfh_shifts

    # Current Month Shifts Calculation
    current_month_str = date.today().strftime("%Y-%m")
    this_month_df = df[df["log_date"].str.startswith(current_month_str)]
    this_month_shifts = len(this_month_df)
    this_month_hours = this_month_df["total_hours"].sum()

    # 5. Display KPI Summary Cards
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(label="Total Shifts Logged", value=total_shifts, delta=f"{this_month_shifts} this month")
    with col_m2:
        st.metric(label="Total Hours Recorded", value=f"{total_hours_worked:.1f} hrs", delta=f"{this_month_hours:.1f} hrs this month")
    with col_m3:
        st.metric(label="Avg Shift Duration", value=f"{avg_hours_per_shift:.1f} hrs")
    with col_m4:
        st.metric(label="On-Site / WFH Ratio", value=f"{on_site_shifts} / {wfh_shifts}")

    st.write("")

    # 6. Detailed Chronological Log Table
    st.subheader(f"📜 Attendance Records for {selected_worker['full_name']}")

    display_df = df[[
        "log_date", "status", "clock_in", "clock_out", "total_hours"
    ]].copy()

    display_df.rename(columns={
        "log_date": "Date",
        "status": "Status",
        "clock_in": "Clock In",
        "clock_out": "Clock Out",
        "total_hours": "Hours Worked"
    }, inplace=True)

    # Clean display values
    display_df["Clock Out"] = display_df["Clock Out"].fillna("--:--")
    display_df["Hours Worked"] = display_df["Hours Worked"].apply(lambda x: f"{x:.2f}")

    styled_worker_df = style_attendance_df(display_df)
    st.dataframe(
        styled_worker_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date": st.column_config.TextColumn(help="Date of shift entry"),
            "Hours Worked": st.column_config.TextColumn(help="Total elapsed duration")
        }
    )

    # 7. CSV Download for Individual Worker History
    csv_worker_data = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"📥 Download History for {selected_worker['full_name']} (CSV)",
        data=csv_worker_data,
        file_name=f"worker_{duty_no}_{selected_worker['full_name'].replace(' ', '_')}_history.csv",
        mime="text/csv",
        use_container_width=False
    )
