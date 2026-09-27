from datetime import date, timedelta
import pandas as pd
import streamlit as st

from src.db import (
    get_all_workers,
    get_daily_punches,
    get_schedules_for_range
)
from src.components import (
    render_page_header,
    merge_roster_and_punches,
    style_attendance_df
)


def render_daily_archive_view() -> None:
    """Renders Tab 2: Daily Attendance Archive, historical date lookup, and CSV export."""
    render_page_header(
        title="Daily Attendance Archive",
        subtitle="Review historical attendance records, daily hours, and export logs to CSV"
    )

    # 1. Date Selection Controls
    col_date, col_preset, _ = st.columns([1.5, 1.5, 2])

    with col_date:
        selected_date = st.date_input(
            "Select Date to Inspect:",
            value=date.today(),
            max_value=date.today(),
            key="archive_date_picker"
        )
        target_date_str = selected_date.isoformat()

    with col_preset:
        st.write("")
        st.write("")
        col_btn_yesterday, col_btn_today = st.columns(2)
        with col_btn_yesterday:
            if st.button("Yesterday", use_container_width=True):
                st.session_state["archive_date_picker"] = date.today() - timedelta(days=1)
                st.rerun()
        with col_btn_today:
            if st.button("Today", use_container_width=True):
                st.session_state["archive_date_picker"] = date.today()
                st.rerun()

    # 2. Fetch Data for Selected Date
    workers = get_all_workers(active_only=False)  # Include past/inactive workers in history
    if not workers:
        st.info("No worker profiles found in the system.")
        return

    punches = get_daily_punches(target_date_str)
    schedules = get_schedules_for_range(target_date_str, target_date_str)

    # Merge into unified table
    df = merge_roster_and_punches(workers, punches, schedules)

    # 3. Calculate Day Summary Analytics
    total_roster = len(workers)
    total_punched = len(punches)
    on_site_count = sum(1 for p in punches if p.get("status") in ["On Duty", "Clocked Out"] and p.get("clock_in"))
    wfh_count = sum(1 for p in punches if p.get("status") == "WFH")
    absent_count = total_roster - total_punched

    # Compute total hours logged on that day
    try:
        total_hours = sum(float(p.get("total_hours") or 0.0) for p in punches)
    except Exception:
        total_hours = 0.0

    # Render Day Metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(label="Total Logged In", value=f"{total_punched} / {total_roster}")
    with col_m2:
        st.metric(label="On-Site / WFH Split", value=f"{on_site_count} / {wfh_count}")
    with col_m3:
        st.metric(label="Total Hours Recorded", value=f"{total_hours:.1f} hrs")
    with col_m4:
        st.metric(label="Unaccounted / Absent", value=max(0, absent_count))

    st.write("")

    # 4. Search & Filter Bar
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_kw = st.text_input("Search worker in this log:", "", key="archive_search").strip().lower()
    with col_filter:
        filter_status = st.selectbox(
            "Filter Status:",
            ["All Records", "Attended (Clocked)", "On Duty", "WFH", "Clocked Out", "Not On Duty"],
            key="archive_status_filter"
        )

    # Filter application
    filtered_df = df.copy()
    if search_kw:
        filtered_df = filtered_df[
            filtered_df["Worker Name"].str.lower().str.contains(search_kw) |
            filtered_df["Duty #"].astype(str).str.contains(search_kw)
        ]

    if filter_status == "Attended (Clocked)":
        filtered_df = filtered_df[filtered_df["Status"] != "Not On Duty"]
    elif filter_status != "All Records":
        filtered_df = filtered_df[filtered_df["Status"] == filter_status]

    # 5. Render Historical Table
    styled_archive_df = style_attendance_df(filtered_df)
    st.dataframe(
        styled_archive_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Duty #": st.column_config.NumberColumn(format="%d"),
            "Hours Worked": st.column_config.TextColumn(help="Calculated upon clock out")
        }
    )

    # 6. CSV Download Action
    st.write("")
    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    
    st.download_button(
        label=f"📥 Download Attendance Log for {target_date_str} (CSV)",
        data=csv_data,
        file_name=f"shifttrack_attendance_{target_date_str}.csv",
        mime="text/csv",
        use_container_width=False
    )
