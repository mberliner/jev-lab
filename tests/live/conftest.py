"""Aborta la sesión antes de empezar si los tests `live` seleccionados superan el tope."""

import os

import pytest

from tests.live.budget import check_budget, parse_budget


def pytest_collection_finish(session: pytest.Session) -> None:
    caps: dict[str, float | None] = {}
    for item in session.items:
        marker = item.get_closest_marker("live")
        if marker is not None:
            cap = marker.kwargs.get("max_usd")
            caps[item.nodeid] = float(cap) if cap is not None else None
    if not caps:
        return
    reason = check_budget(caps, parse_budget(os.environ.get("JEVLAB_LIVE_BUDGET_USD")))
    if reason is not None:
        pytest.exit(reason, returncode=pytest.ExitCode.USAGE_ERROR)
