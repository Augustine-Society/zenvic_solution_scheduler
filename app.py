import streamlit as st

# 1. Page Configuration (Must be the first Streamlit command)
st.set_page_config(
    page_title="ShiftTrack | Kiosk & Supervisor Board",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. View Imports
from src.views.live_station import render_live_station_view
from src.views.daily_archive import render_daily_archive_view
from src.views.worker_audit import render_worker_audit_view
from src.views.roster_manager import render_roster_manager_view
from src.db import add_worker, get_all_workers


def main():
    # Application Title & Global Navigation
    st.sidebar.title("⏱️ ShiftTrack")
    st.sidebar.caption("Cloud Attendance & Roster System")
    st.sidebar.divider()

    # Quick Refresh Action
    if st.sidebar.button("🔄 Sync / Refresh Data", use_container_width=True):
        st.rerun()

    # Quick Worker Registration Drawer
    with st.sidebar.expander("➕ Register New Worker", expanded=False):
        new_duty_no = st.number_input("Duty Number:", min_value=1, step=1, value=105)
        new_name = st.text_input("Full Name:", "")
        new_dept = st.selectbox("Department:", ["Operations", "Engineering", "Logistics", "Support", "General"])

        if st.button("Register Worker", use_container_width=True):
            if new_name.strip():
                if add_worker(int(new_duty_no), new_name, new_dept):
                    st.success(f"Worker #{new_duty_no} registered!")
                    st.rerun()
            else:
                st.error("Please enter a worker name.")

    # Status / Cloud Connection Indicator in Sidebar
    workers = get_all_workers(active_only=True)
    st.sidebar.divider()
    st.sidebar.caption(f"⚡ Connected to Supabase Cloud")
    st.sidebar.caption(f"👥 Active Roster: **{len(workers)} workers**")

    # Top-level Tab Navigation
    tab1, tab2, tab3, tab4 = st.tabs([
        "📍 Live Station (Kiosk)",
        "📅 Daily Log Archive",
        "👤 Worker-Wise Audit",
        "🗓️ Weekly Roster Manager"
    ])

    with tab1:
        render_live_station_view()

    with tab2:
        render_daily_archive_view()

    with tab3:
        render_worker_audit_view()

    with tab4:
        render_roster_manager_view()


if __name__ == "__main__":
    main()
