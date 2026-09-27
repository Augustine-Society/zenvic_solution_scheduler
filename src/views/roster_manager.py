from datetime import date, timedelta, time
import pandas as pd
import streamlit as st

from src.db import (
    get_all_workers,
    get_schedules_for_range,
    upsert_schedule
)
from src.components import render_page_header


def get_week_bounds(target_date: date) -> tuple[date, date]:
    """Returns the Monday and Sunday dates for the given date's week."""
    monday = target_date - timedelta(days=target_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def render_roster_manager_view() -> None:
    """Renders Tab 4: Weekly shift planning matrix and supervisor duty assignment form."""
    render_page_header(
        title="Weekly Duty Roster & Planning",
        subtitle="Schedule upcoming shifts, designate On-Site vs. WFH, and manage weekly rotations"
    )

    # 1. Fetch Workers
    workers = get_all_workers(active_only=True)
    if not workers:
        st.warning("No active workers found in the directory.")
        return

    # 2. Week Selection
    today = date.today()
    this_monday, this_sunday = get_week_bounds(today)
    next_monday, next_sunday = this_monday + timedelta(days=7), this_sunday + timedelta(days=7)

    col_toggle, _ = st.columns([2, 2])
    with col_toggle:
        week_choice = st.radio(
            "Select Roster Week:",
            options=[
                f"Current Week ({this_monday.strftime('%b %d')} - {this_sunday.strftime('%b %d')})",
                f"Next Week ({next_monday.strftime('%b %d')} - {next_sunday.strftime('%b %d')})"
            ],
            horizontal=True
        )

    if "Current Week" in week_choice:
        start_dt, end_dt = this_monday, this_sunday
    else:
        start_dt, end_dt = next_monday, next_sunday

    start_str = start_dt.isoformat()
    end_str = end_dt.isoformat()

    # 3. Fetch Existing Schedules for Selected Week
    schedules = get_schedules_for_range(start_str, end_str)

    # Map (duty_number, shift_date) -> formatted shift string
    schedule_map = {}
    for s in schedules:
        d_no = s["duty_number"]
        s_date = s["shift_date"]
        s_type = s.get("shift_type", "On-Site")
        if s_type == "Rest Day":
            label = "🛑 Rest Day"
        else:
            t_start = s.get("start_time") or "09:00"
            t_end = s.get("end_time") or "17:00"
            # Format to HH:MM if string has seconds
            t_start = t_start[:5]
            t_end = t_end[:5]
            badge = "🟢" if s_type == "On-Site" else "🔵"
            label = f"{badge} {s_type} ({t_start}-{t_end})"
        schedule_map[(d_no, s_date)] = label

    # 4. Build Mon–Sun Matrix
    days_of_week = [start_dt + timedelta(days=i) for i in range(7)]
    day_columns = [d.strftime("%a (%b %d)") for d in days_of_week]

    matrix_rows = []
    for w in workers:
        row = {
            "Duty #": w["duty_number"],
            "Worker Name": w["full_name"],
            "Dept": w.get("department", "General")
        }
        for d in days_of_week:
            col_name = d.strftime("%a (%b %d)")
            cell_value = schedule_map.get((w["duty_number"], d.isoformat()), "— Not Set —")
            row[col_name] = cell_value
        matrix_rows.append(row)

    matrix_df = pd.DataFrame(matrix_rows)

    # Render Weekly Schedule Matrix
    st.subheader(f"📅 Roster Matrix ({start_str} to {end_str})")
    st.dataframe(
        matrix_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Duty #": st.column_config.NumberColumn(format="%d")
        }
    )

    st.write("")

    # 5. Shift Assignment Form (Supervisor Action)
    with st.container(border=True):
        st.subheader("✍️ Assign or Update Shift")
        st.caption("Assign work hours and duty type for a worker on a specific date. Changes sync instantly to all devices.")

        worker_options = {
            f"#{w['duty_number']} - {w['full_name']}": w['duty_number']
            for w in workers
        }

        col_w, col_d = st.columns(2)
        with col_w:
            chosen_worker_label = st.selectbox("Worker:", options=list(worker_options.keys()), key="roster_worker_select")
            target_duty_no = worker_options[chosen_worker_label]

        with col_d:
            chosen_date = st.date_input(
                "Shift Date:",
                value=start_dt,
                min_value=start_dt,
                max_value=end_dt,
                key="roster_date_select"
            )

        col_type, col_start, col_end = st.columns(3)
        with col_type:
            shift_type = st.selectbox(
                "Duty / Shift Type:",
                options=["On-Site", "WFH", "Rest Day"],
                key="roster_type_select"
            )

        is_rest = shift_type == "Rest Day"
        with col_start:
            start_val = st.time_input("Start Time:", value=time(9, 0), disabled=is_rest)
        with col_end:
            end_val = st.time_input("End Time:", value=time(17, 0), disabled=is_rest)

        st.write("")
        if st.button("💾 Save Shift to Roster", use_container_width=True, type="primary"):
            t_start_str = start_val.strftime("%H:%M") if not is_rest else None
            t_end_str = end_val.strftime("%H:%M") if not is_rest else None

            success = upsert_schedule(
                duty_number=target_duty_no,
                shift_date=chosen_date.isoformat(),
                shift_type=shift_type,
                start_time=t_start_str,
                end_time=t_end_str
            )
            if success:
                st.toast(f"Shift updated for Duty #{target_duty_no} on {chosen_date.isoformat()}!", icon="✅")
                st.rerun()
