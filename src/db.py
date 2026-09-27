from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase_client() -> Client:
    """Initialize and cache the Supabase client using secrets or fallback keys."""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    except Exception:
        # Fallback to direct credentials if secrets.toml is not loaded
        url = "https://dmvdhuaysbimgwbfwydo.supabase.co"
        key = "sb_publishable_UTSSYpx9YQxMWP5m0I49Yw_qtBAuSMJ"
    return create_client(url, key)


client: Client = get_supabase_client()


# ==========================================
# 1. WORKERS QUERIES
# ==========================================

def get_all_workers(active_only: bool = True) -> List[Dict[str, Any]]:
    """Fetch registered workers from the workers table."""
    query = client.table("workers").select("*")
    if active_only:
        query = query.eq("is_active", True)
    response = query.order("duty_number").execute()
    return response.data or []


def add_worker(duty_number: int, full_name: str, department: str = "General") -> bool:
    """Add a new worker to the directory."""
    try:
        data = {
            "duty_number": duty_number,
            "full_name": full_name.strip(),
            "department": department.strip(),
            "is_active": True
        }
        client.table("workers").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error adding worker: {e}")
        return False


# ==========================================
# 2. PUNCH LOGS & ATTENDANCE QUERIES
# ==========================================

def get_worker_today_punch(duty_number: int, target_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve punch status for a specific worker on a given date."""
    if not target_date:
        target_date = date.today().isoformat()

    response = (
        client.table("punch_logs")
        .select("*")
        .eq("duty_number", duty_number)
        .eq("log_date", target_date)
        .execute()
    )
    return response.data[0] if response.data else None


def clock_in_worker(duty_number: int, mode: str = "On Duty") -> Dict[str, Any]:
    """
    Clock in a worker for today.
    mode can be 'On Duty' or 'WFH'
    """
    today_str = date.today().isoformat()
    now_time_str = datetime.now().strftime("%H:%M:%S")

    # Check for existing punch
    existing = get_worker_today_punch(duty_number, today_str)
    if existing:
        return {"success": False, "message": f"Already clocked in as {existing.get('status')} at {existing.get('clock_in')}"}

    payload = {
        "duty_number": duty_number,
        "log_date": today_str,
        "status": mode,
        "clock_in": now_time_str,
        "clock_out": None,
        "total_hours": 0.0
    }

    try:
        client.table("punch_logs").insert(payload).execute()
        return {"success": True, "message": f"Clocked in as {mode} at {now_time_str}", "time": now_time_str}
    except Exception as e:
        return {"success": False, "message": str(e)}


def clock_out_worker(duty_number: int) -> Dict[str, Any]:
    """Clock out a worker and compute total worked hours."""
    today_str = date.today().isoformat()
    now_dt = datetime.now()
    now_time_str = now_dt.strftime("%H:%M:%S")

    existing = get_worker_today_punch(duty_number, today_str)
    if not existing:
        return {"success": False, "message": "No active clock-in found for today."}

    if existing.get("status") == "Clocked Out":
        return {"success": False, "message": f"Already clocked out at {existing.get('clock_out')}."}

    # Calculate hours worked
    clock_in_str = existing.get("clock_in")
    try:
        t_in = datetime.strptime(clock_in_str, "%H:%M:%S")
        t_out = datetime.strptime(now_time_str, "%H:%M:%S")
        duration = (t_out - t_in).total_seconds()
        if duration < 0:
            duration += 86400  # Shift crossed midnight
        hours = round(duration / 3600.0, 2)
    except Exception:
        hours = 0.0

    update_payload = {
        "status": "Clocked Out",
        "clock_out": now_time_str,
        "total_hours": hours
    }

    try:
        client.table("punch_logs").update(update_payload).eq("id", existing["id"]).execute()
        return {"success": True, "message": f"Clocked out at {now_time_str} (Total: {hours} hrs)", "time": now_time_str, "hours": hours}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_daily_punches(target_date: str) -> List[Dict[str, Any]]:
    """Retrieve all punch records for a specific calendar date."""
    response = client.table("punch_logs").select("*").eq("log_date", target_date).execute()
    return response.data or []


def get_worker_punches_history(duty_number: int) -> List[Dict[str, Any]]:
    """Retrieve all historical punches for a specific worker."""
    response = (
        client.table("punch_logs")
        .select("*")
        .eq("duty_number", duty_number)
        .order("log_date", desc=True)
        .execute()
    )
    return response.data or []


# ==========================================
# 3. SCHEDULES & ROSTER QUERIES
# ==========================================

def get_schedules_for_range(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Fetch forward scheduled duties between two dates."""
    response = (
        client.table("schedules")
        .select("*")
        .gte("shift_date", start_date)
        .lte("shift_date", end_date)
        .execute()
    )
    return response.data or []


def upsert_schedule(duty_number: int, shift_date: str, shift_type: str, start_time: str, end_time: str) -> bool:
    """Assign or update a worker's shift assignment."""
    payload = {
        "duty_number": duty_number,
        "shift_date": shift_date,
        "shift_type": shift_type,
        "start_time": start_time,
        "end_time": end_time
    }
    try:
        client.table("schedules").upsert(payload, on_conflict="duty_number, shift_date").execute()
        return True
    except Exception as e:
        st.error(f"Failed to update schedule: {e}")
        return False
