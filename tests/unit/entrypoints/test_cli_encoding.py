"""La CLI escribe en UTF-8 también por una tubería de Windows (research.md R7)."""

import io
import sys

import pytest
from typer.testing import CliRunner

import jevlab.entrypoints.cli.main as cli
from tests.fakes import FakeGeneratorProbe, FakeLocalEnvironment, FakeModelCatalog


def test_reconfigures_cp1252_streams_to_utf8(monkeypatch: pytest.MonkeyPatch) -> None:
    out = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    err = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)

    cli.configure_output_encoding()

    assert out.encoding == "utf-8"
    assert err.encoding == "utf-8"
    out.write("Urgencia explícita · sí")
    out.flush()
    assert out.buffer.getvalue().decode("utf-8") == "Urgencia explícita · sí"


def test_streams_without_reconfigure_are_left_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdout", io.StringIO())
    cli.configure_output_encoding()


def test_every_command_configures_the_encoding(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []
    monkeypatch.setattr(cli, "configure_output_encoding", lambda: calls.append(True))
    adapters = (FakeLocalEnvironment(), FakeModelCatalog(), FakeGeneratorProbe())
    monkeypatch.setattr(cli, "build_adapters", lambda: adapters)

    result = CliRunner().invoke(cli.app, ["doctor"])

    assert result.exit_code == 0
    assert calls == [True]
