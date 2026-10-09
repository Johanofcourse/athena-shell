import ipaddress
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import QueryUsage

FREE_DAILY_QUERY_LIMIT = 10


def _is_exempt(ip: str) -> bool:
    """Loopback (127.0.0.1, ::1) is unmetered - needed for local dev/testing,
    where the same machine legitimately runs hundreds of queries a day.
    This is safe for local development: once actually deployed (Phase 5),
    real client IPs won't be loopback addresses, and in production nginx
    + ProxyHeadersMiddleware correctly resolve the real client IP rather
    than nginx's own loopback address - confirmed directly against the
    live QueryUsage table, not assumed. `exempt_ips` (settings) is the
    same idea for real, named IPs - e.g. Johan's own - that also shouldn't
    count against the free cap; checked here rather than in a separate
    code path so both exemptions share one `allowed, remaining_today`
    contract."""
    if ip in settings.exempt_ip_set:
        return True
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
