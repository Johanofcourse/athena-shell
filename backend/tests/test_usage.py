"""Tests for app/usage.py - the free-tier daily query cap behind POST
/query. db_session (not seeded_db) is enough here: QueryUsage doesn't
reference any metro data."""

from app.config import settings
from app.usage import FREE_DAILY_QUERY_LIMIT, check_and_increment_usage


def test_allows_up_to_the_daily_limit_then_blocks(db_session):
    ip = "203.0.113.5"  # TEST-NET-3 (RFC 5737) - not a real, routable address
    for i in range(FREE_DAILY_QUERY_LIMIT):
        allowed, remaining = check_and_increment_usage(db_session, ip)
        assert allowed is True
        assert remaining == FREE_DAILY_QUERY_LIMIT - (i + 1)

    allowed, remaining = check_and_increment_usage(db_session, ip)
    assert allowed is False
    assert remaining == 0


def test_loopback_is_unmetered(db_session):
    for _ in range(FREE_DAILY_QUERY_LIMIT + 5):
        allowed, _ = check_and_increment_usage(db_session, "127.0.0.1")
        assert allowed is True


def test_configured_exempt_ip_is_unmetered(db_session, monkeypatch):
    # Real case this covers: Johan's own IP, set via the server's own
    # .env (EXEMPT_IPS), never committed - same reasoning as any other
    # secret/identifying value here.
    monkeypatch.setattr(settings, "exempt_ips", "198.51.100.9")
    for _ in range(FREE_DAILY_QUERY_LIMIT + 5):
        allowed, _ = check_and_increment_usage(db_session, "198.51.100.9")
        assert allowed is True


def test_exempt_ips_does_not_exempt_other_ips(db_session, monkeypatch):
    # A real bug this guards against: a set-membership check that
    # accidentally matches everything (e.g. a substring check instead of
    # exact match) would silently uncap the whole free tier.
    monkeypatch.setattr(settings, "exempt_ips", "198.51.100.9")
    for i in range(FREE_DAILY_QUERY_LIMIT):
        allowed, _ = check_and_increment_usage(db_session, "203.0.113.5")
        assert allowed is True

    allowed, remaining = check_and_increment_usage(db_session, "203.0.113.5")
    assert allowed is False
    assert remaining == 0


def test_exempt_ips_parses_a_comma_separated_list(db_session, monkeypatch):
    monkeypatch.setattr(settings, "exempt_ips", "198.51.100.9, 198.51.100.10 ,198.51.100.11")
    assert settings.exempt_ip_set == {"198.51.100.9", "198.51.100.10", "198.51.100.11"}
