from datetime import datetime, timedelta
import pytz

def get_local_time(utc_time_str, local_tz_name="UTC"):
    """
    Converts UTC ISO string to local datetime.
    """
    utc_tz = pytz.utc
    local_tz = pytz.timezone(local_tz_name)
    
    utc_dt = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
    local_dt = utc_dt.astimezone(local_tz)
    return local_dt

def to_utc_str(dt, local_tz_name="UTC"):
    """
    Converts local datetime to UTC ISO string.
    """
    local_tz = pytz.timezone(local_tz_name)
    if dt.tzinfo is None:
        dt = local_tz.localize(dt)
    utc_dt = dt.astimezone(pytz.utc)
    return utc_dt.isoformat()

def get_week_days(start_date=None):
    """
    Returns a list of dates for the current week (starting Monday).
    """
    if start_date is None:
        start_date = datetime.now()
    
    # Monday is 0
    monday = start_date - timedelta(days=start_date.weekday())
    return [monday + timedelta(days=i) for i in range(7)]

def format_time(dt):
    return dt.strftime("%H:%M")

def get_time_slots():
    """Returns 30-min intervals as strings"""
    slots = []
    for h in range(24):
        slots.append(f"{h:02d}:00")
        slots.append(f"{h:02d}:30")
    return slots
