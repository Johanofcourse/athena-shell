import ipaddress
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import QueryUsage

FREE_DAILY_QUERY_LIMIT = 10


def _is_exempt(ip: str) -> bool:
    """Loopback (127.0.0.1, ::1) is unmetered - needed for local dev/testing,
    where the same machine legitimately runs hundreds of queries a day.
    This is safe for local development: once actually deployed (Phase 5),
    real client IPs won't be loopback addresses. If a reverse proxy is ever
    added in front of this, the IP extraction (get_remote_address) and this
    exemption both need revisiting together - a misconfigured proxy could
    make every request look like it's from loopback."""
    try:
        return ipaddress.ip_address(ip).is_loopback
    except ValueError:
        return False


def check_and_increment_usage(db: Session, ip: str) -> tuple[bool, int]:
    """Returns (allowed, remaining_today). Resets at UTC midnight - a
    calendar-day quota is easier to state honestly to a user ("resets
    tomorrow") than a rolling 24h window."""
    if _is_exempt(ip):
        return True, FREE_DAILY_QUERY_LIMIT

    today = datetime.now(timezone.utc).date()
    row = db.get(QueryUsage, (ip, today))
    if row is None:
        row = QueryUsage(ip=ip, date=today, count=0)
        db.add(row)

    if row.count >= FREE_DAILY_QUERY_LIMIT:
        return False, 0

    row.count += 1
    db.commit()
    return True, FREE_DAILY_QUERY_LIMIT - row.count
