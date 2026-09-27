from typing import List, Dict, Any, Tuple
import pandas as pd
import streamlit as st


# ==========================================
# 1. STATUS BADGES & VISUAL FORMATTERS
# ==========================================

STATUS_COLORS = {
    "On Duty": "#22c55e",       # Vivid Green
    "WFH": "#3b82f6",           # Blue
    "Not On Duty": "#9ca3af",   # Muted Gray
    "Clocked Out": "#ef4444",   # Soft Red
    "Rest Day": "#6b7280"       # Dark Gray
}


def render_status_badge(status: str) -> str:
    """Generate a clean HTML badge for a status string."""
    color = STATUS_COLORS.get(status, "#9ca3af")
    return (
        f'<span style="background-color: {color}20; color: {color}; '
        f'padding: 4px 10px; border-radius: 9999px; font-weight: 600; '
        f'font-size: 0.85rem; border: 1px solid {color}40;">'
        f'{status}</span>'
    )


def style_attendance_df(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    """
    Applies color styling to status columns in Pandas DataFrames for Streamlit tables.
    """
    def highlight_status(val):
        color = STATUS_COLORS.get(val, "transparent")
        if color != "transparent":
            return f"background-color: {color}22; color: {color}; font-weight: bold;"
        return ""

    if "Status" in df.columns:
        return df.style.map(highlight_status, subset=["Status"])
    return df.style


# ==========================================
# 2. KPI METRIC SUMMARY CARDS
# ==========================================

def render_kpi_metrics(workers: List[Dict[str, Any]], punches: List[Dict[str, Any]]) -> None:
    """
    Computes and displays top-bar KPI metrics:
    - Active On-Site
    - Active WFH
    - Completed (Clocked Out)
    - Not Yet Arrived / Off
    """
    total_workers = len(workers)
    
    # Map duty_number to today's status
    punch_map = {p["duty_number"]: p["status"] for p in punches}
    
    on_duty_count = sum(1 for status in punch_map.values() if status == "On Duty")
    wfh_count = sum(1 for status in punch_map.values() if status == "WFH")
    clocked_out_count = sum(1 for status in punch_map.values() if status == "Clocked Out")
    not_arrived_count = total_workers - (on_duty_count + wfh_count + clocked_out_count)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="🟢 On-Site (Active)", value=on_duty_count)
    with col2:
        st.metric(label="🔵 WFH (Remote)", value=wfh_count)
    with col3:
        st.metric(label="🔴 Clocked Out", value=clocked_out_count)
    with col4:
        st.metric(label="⚪ Not Arrived / Off", value=max(0, not_arrived_count))


# ==========================================
# 3. DATA MERGER & TABLE PREPARATION
# ==========================================

def merge_roster_and_punches(
    workers: List[Dict[str, Any]],
    punches: List[Dict[str, Any]],
    schedules: List[Dict[str, Any]]
) -> pd.DataFrame:
    """
    Combines workers, daily punch logs, and planned schedules into a single clean DataFrame.
    """
    punch_map = {p["duty_number"]: p for p in punches}
    schedule_map = {s["duty_number"]: s for s in schedules}

    rows = []
    for w in workers:
        duty_no = w["duty_number"]
        name = w["full_name"]
        dept = w.get("department", "General")

        # Schedule info
        sched = schedule_map.get(duty_no)
        if sched:
            sched_shift = f"{sched.get('start_time', '--')} - {sched.get('end_time', '--')} ({sched.get('shift_type', 'Shift')})"
        else:
            sched_shift = "Regular (Not Assigned)"

        # Punch info
        punch = punch_map.get(duty_no)
        if punch:
            status = punch.get("status", "Not On Duty")
            clock_in = punch.get("clock_in") or "--:--"
            clock_out = punch.get("clock_out") or "--:--"
            hours = f"{punch.get('total_hours', 0.0):.2f}"
        else:
            status = "Not On Duty"
            clock_in = "--:--"
            clock_out = "--:--"
            hours = "0.00"

        rows.append({
            "Duty #": duty_no,
            "Worker Name": name,
            "Department": dept,
            "Assigned Shift": sched_shift,
            "Status": status,
            "Clock In": clock_in,
            "Clock Out": clock_out,
            "Hours Worked": hours
        })

    return pd.DataFrame(rows)


def render_page_header(title: str, subtitle: str) -> None:
    """Consistent header component across all views."""
    st.markdown(f"### {title}")
    st.caption(subtitle)
    st.divider()
