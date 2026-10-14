from datetime import date

from jevlab.adapters.system_clock import SystemClock


def test_today_is_a_date() -> None:
    today = SystemClock().today()
    assert isinstance(today, date)
    assert today == date.today()
