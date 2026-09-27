from datetime import date
import streamlit as st

from src.db import (
    get_all_workers,
    get_daily_punches,
    get_schedules_for_range,
    get_worker_today_punch,
    clock_in_worker,
    clock_out_worker
)
from src.components import (
    render_page_header,
    render_kpi_metrics,
    merge_roster_and_punches,
    style_attendance_df
)


def render_live_station_view() -> None:
    """Renders Tab 1: Live Punch Station and Real-Time Roster Dashboard."""
    today_str = date.today().isoformat()

    render_page_header(
        title="Live Punch Station & Attendance Board",
        subtitle=f"Real-time walk-up check-in and presence tracking for {today_str}"
    )

    # 1. Fetch current live data from Supabase
    workers = get_all_workers(active_only=True)
    if not workers:
        st.warning("No active workers found in the database. Please add workers in the database first.")
        return

    punches = get_daily_punches(today_str)
    schedules = get_schedules_for_range(today_str, today_str)

    # 2. Render Real-time KPI Metric Summary Cards
    render_kpi_metrics(workers, punches)
    st.write("")

    # 3. Walk-Up Punch Action Card
    with st.container(border=True):
        st.subheader("⏱️ Walk-Up Punch Station")
        st.caption("Select your name or duty number, choose your work mode, and punch in or out.")

        col_select, col_mode = st.columns([2, 1])

        # Create worker dropdown labels
        worker_options = {
            f"#{w['duty_number']} - {w['full_name']} ({w.get('department', 'General')})": w['duty_number']
            for w in workers
        }

        with col_select:
            selected_label = st.selectbox(
                "Select Worker Identity:",
                options=list(worker_options.keys()),
                index=0,
                key="kiosk_worker_select"
            )
            selected_duty_no = worker_options[selected_label]

        # Inspect current instantaneous status of the selected worker
        current_punch = get_worker_today_punch(selected_duty_no, today_str)
        is_clocked_in = current_punch is not None and current_punch.get("status") in ["On Duty", "WFH"]
        is_clocked_out = current_punch is not None and current_punch.get("status") == "Clocked Out"

        with col_mode:
            # Mode toggle (locked if worker has already punched in)
            default_mode_index = 1 if (current_punch and current_punch.get("status") == "WFH") else 0
            duty_mode = st.radio(
                "Duty Mode:",
                options=["On Duty", "WFH"],
                index=default_mode_index,
                horizontal=True,
                disabled=is_clocked_in or is_clocked_out,
                help="Choose On-Site vs. Work From Home"
            )

        # Status badge summary for the selected user
        if is_clocked_in:
            st.info(f"Currently active: **{current_punch.get('status')}** since **{current_punch.get('clock_in')}**")
        elif is_clocked_out:
            st.success(f"Shift completed: Clocked out at **{current_punch.get('clock_out')}** (Total: {current_punch.get('total_hours')} hrs)")
        else:
            st.warning("Not clocked in today.")

        # Punch Action Buttons
        col_btn1, col_btn2, _ = st.columns([1, 1, 2])

        with col_btn1:
            # Clock In Button (disabled if already clocked in or clocked out)
            clock_in_disabled = is_clocked_in or is_clocked_out
            if st.button("🟢 Clock In", disabled=clock_in_disabled, use_container_width=True):
                result = clock_in_worker(selected_duty_no, mode=duty_mode)
                if result.get("success"):
                    st.toast(result.get("message"), icon="✅")
                    st.rerun()
                else:
                    st.error(result.get("message"))

        with col_btn2:
            # Clock Out Button (disabled if not on duty)
            clock_out_disabled = not is_clocked_in
            if st.button("🔴 Clock Out", disabled=clock_out_disabled, use_container_width=True):
                result = clock_out_worker(selected_duty_no)
                if result.get("success"):
                    st.toast(result.get("message"), icon="🚪")
                    st.rerun()
                else:
                    st.error(result.get("message"))

    st.write("")

    # 4. Live Attendance Board
    st.subheader("📋 Today's Live Attendance Board")
    
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("🔍 Quick Search by Name or Duty #", "").strip().lower()
    with col_filter:
        status_filter = st.selectbox("Filter by Status", ["All Statuses", "On Duty", "WFH", "Not On Duty", "Clocked Out"])

    # Prepare DataFrame
    df = merge_roster_and_punches(workers, punches, schedules)

    # Apply search and status filters
    if search_query:
        df = df[
            df["Worker Name"].str.lower().str.contains(search_query) |
            df["Duty #"].astype(str).str.contains(search_query)
        ]

    if status_filter != "All Statuses":
        df = df[df["Status"] == status_filter]

    # Render styled table
    styled_df = style_attendance_df(df)
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Duty #": st.column_config.NumberColumn(format="%d"),
            "Hours Worked": st.column_config.TextColumn(help="Hours computed upon Clock Out")
        }
    )
