"""Logs del SDK sin payloads por defecto (research.md R12, docs/standards/security.md §2)."""

import logging
from collections.abc import Iterator

import httpx2
import pytest
from typer.testing import CliRunner

import jevlab.entrypoints.cli.main as cli
from jevlab.adapters.typesafe_catalog import TypeSafeModelCatalog
from tests.fakes import FakeGeneratorProbe, FakeLocalEnvironment, FakeModelCatalog

# Respuesta sintética: no procede de TypeSafe.
_MARKER = "PAYLOAD-SINTETICO-QUE-NO-DEBE-APARECER"
_SDK_LOGGER = logging.getLogger("typesafe_sdk")


@pytest.fixture(autouse=True)
def _restore_sdk_level() -> Iterator[None]:
    level = _SDK_LOGGER.level
    yield
    _SDK_LOGGER.setLevel(level)


def _run_doctor(monkeypatch: pytest.MonkeyPatch) -> None:
    adapters = (FakeLocalEnvironment(), FakeModelCatalog(), FakeGeneratorProbe())
    monkeypatch.setattr(cli, "build_adapters", lambda: adapters)
    CliRunner().invoke(cli.app, ["doctor"])


def _handler(request: httpx2.Request) -> httpx2.Response:
    body = {"models": [{"name": "jev-1.13", "description": _MARKER, "release_date": "2026-01-01"}]}
    return httpx2.Response(200, json=body)


def test_cli_sets_sdk_logger_to_warning_and_hides_payloads(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.delenv("TYPESAFE_LOG_LEVEL", raising=False)
    _SDK_LOGGER.setLevel(logging.DEBUG)

    _run_doctor(monkeypatch)

    assert _SDK_LOGGER.level == logging.WARNING
    caplog.set_level(logging.DEBUG)
    catalog = TypeSafeModelCatalog(
        api_key="clave-de-prueba", model=None, transport=httpx2.MockTransport(_handler)
    )
    assert catalog.list_models() == ["jev-1.13"]
    assert _MARKER not in caplog.text


def test_cli_respects_explicit_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TYPESAFE_LOG_LEVEL", "debug")
    _SDK_LOGGER.setLevel(logging.DEBUG)

    _run_doctor(monkeypatch)

    assert _SDK_LOGGER.level == logging.DEBUG
