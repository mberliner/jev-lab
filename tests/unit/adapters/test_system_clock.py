from datetime import UTC, date, datetime, timedelta

from jevlab.adapters.system_clock import SystemClock


def test_today_is_a_date() -> None:
    today = SystemClock().today()
    assert isinstance(today, date)
    assert today == date.today()


def test_now_is_aware_utc() -> None:
    now = SystemClock().now()
    assert now.tzinfo is UTC
    assert abs(datetime.now(UTC) - now) < timedelta(seconds=5)
