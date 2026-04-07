from datetime import datetime

KEYWORDS = {
    "urgent": "High",
    "broken": "High",
    "not working": "High",
    "crash": "High",
    "error": "High",
    "fail": "High",
    "slow": "Medium",
    "delay": "Medium",
    "issue": "Medium",
    "query": "Low",
    "info": "Low",
    "question": "Low",
}

SLA_LIMITS = {"High": 2, "Medium": 24, "Low": 72}


def auto_priority(complaint_text):
    """Return priority level for complaint text using keyword lookup."""
    lowered_text = complaint_text.lower()
    for keyword, level in KEYWORDS.items():
        if keyword in lowered_text:
            return level
    return "Low"


def check_sla_color(priority, created_at):
    """Return SLA color tag name when ticket age exceeds configured limit."""
    hours_old = (datetime.now() - created_at).total_seconds() / 3600
    limit = SLA_LIMITS.get(priority, 72)
    if hours_old <= limit:
        return ""
    color_map = {"High": "red", "Medium": "orange", "Low": "yellow"}
    return color_map.get(priority, "")


def format_datetime(dt_value):
    """Format datetime values for display in tables and labels."""
    if not dt_value:
        return ""
    if isinstance(dt_value, str):
        parsed = datetime.fromisoformat(dt_value)
        return parsed.strftime("%d %b %Y %H:%M")
    return dt_value.strftime("%d %b %Y %H:%M")
