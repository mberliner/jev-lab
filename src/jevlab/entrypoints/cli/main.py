"""CLI `jevlab`: punto de entrada y cableado de los casos de uso."""

import logging
import os
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import typer

from jevlab.adapters.azure_probe import AzureGeneratorProbe
from jevlab.adapters.local_environment import SystemLocalEnvironment
from jevlab.adapters.settings import ProviderSettings
from jevlab.adapters.typesafe_catalog import TypeSafeModelCatalog
from jevlab.application.check_environment import CheckEnvironment
from jevlab.domain.diagnostics import CheckStatus, DoctorReport
from jevlab.ports.environment import LocalEnvironment
from jevlab.ports.providers import GeneratorProbe, ModelCatalog

app = typer.Typer(
    help="Laboratorio de Jev (TypeSafe).",
    no_args_is_help=True,
    add_completion=False,
)

_TAGS = {CheckStatus.OK: "[ok]", CheckStatus.FAIL: "[fail]", CheckStatus.UNAVAILABLE: "[n/d]"}
_TAG_WIDTH = 7
_NAME_WIDTH = 16


def configure_sdk_logging() -> None:
    """El SDK registra los payloads en DEBUG: por defecto, WARNING (research.md R12)."""
    if not os.environ.get("TYPESAFE_LOG_LEVEL"):
        logging.getLogger("typesafe_sdk").setLevel(logging.WARNING)


def build_adapters() -> tuple[LocalEnvironment, ModelCatalog, GeneratorProbe]:
    """Adaptadores reales; los remotos solo abren conexiones si se les llama."""
    settings = ProviderSettings()
    return (
        SystemLocalEnvironment(root=Path.cwd()),
        TypeSafeModelCatalog(
            api_key=settings.typesafe_api_key, model=settings.typesafe_default_model
        ),
        AzureGeneratorProbe(
            endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            deployment=settings.azure_openai_deployment,
            api_version=settings.azure_openai_api_version,
        ),
    )


def render(report: DoctorReport) -> list[str]:
    lines = []
    for result in report.results:
        tag = _TAGS[result.status].ljust(_TAG_WIDTH)
        lines.append(f"{tag}{result.name.ljust(_NAME_WIDTH)}{result.detail}".rstrip())
        if result.fix:
            lines.append(f"{' ' * _TAG_WIDTH}arreglo: {result.fix}")
    lines.append(_summary(report))
    return lines


def _summary(report: DoctorReport) -> str:
    fails = sum(r.status is CheckStatus.FAIL for r in report.results)
    unavailable = sum(r.status is CheckStatus.UNAVAILABLE for r in report.results)
    parts = []
    if fails:
        parts.append(f"{fails} falla" + ("s" if fails > 1 else ""))
    if unavailable:
        parts.append(f"{unavailable} no disponible" + ("s" if unavailable > 1 else ""))
    return "Resultado: " + (", ".join(parts) if parts else "todo correcto")


def _print_version(value: bool) -> None:
    if value:
        typer.echo(f"jevlab {version('jevlab')}")
        raise typer.Exit()


@app.callback()
def main(
    show_version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Muestra la versión y termina.",
            callback=_print_version,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Laboratorio de Jev (TypeSafe)."""
    configure_sdk_logging()


@app.command()
def doctor(
    remote: Annotated[
        bool,
        typer.Option("--remote", help="Comprueba también el acceso a TypeSafe y a Azure OpenAI."),
    ] = False,
) -> None:
    """Comprueba que el entorno está listo; sin --remote no usa la red."""
    local, catalog, generator = build_adapters()
    report = CheckEnvironment(local=local, catalog=catalog, generator=generator).run(remote)
    for line in render(report):
        typer.echo(line)
    raise typer.Exit(report.exit_code())
