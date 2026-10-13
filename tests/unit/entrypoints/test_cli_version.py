from importlib.metadata import version

from typer.testing import CliRunner

from jevlab.entrypoints.cli.main import app


def test_version_prints_package_version_and_exits_zero() -> None:
    result = CliRunner().invoke(app, ["--version"])

    assert result.exit_code == 0
    assert version("jevlab") in result.output
