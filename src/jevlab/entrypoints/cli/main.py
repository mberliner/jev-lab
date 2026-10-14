"""CLI `jevlab`: punto de entrada y cableado de los casos de uso."""

import logging
import os
import sys
from contextlib import AbstractContextManager
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, TextIO

import typer

from jevlab.adapters.azure_probe import AzureGeneratorProbe
from jevlab.adapters.local_environment import SystemLocalEnvironment
from jevlab.adapters.settings import ProviderSettings
from jevlab.adapters.typesafe_catalog import TypeSafeModelCatalog
from jevlab.adapters.typesafe_judge import TypeSafeJudge
from jevlab.adapters.yaml_files import YamlRecordingLibrary, YamlSpecLoader
from jevlab.application.check_environment import CheckEnvironment
from jevlab.application.triage import TriageTicket
from jevlab.domain.diagnostics import (
    CheckStatus,
    DoctorReport,
    InvalidProviderResponse,
    MissingApiKey,
    ProviderRejected,
    ProviderUnavailable,
    RecordingOutdated,
)
from jevlab.domain.examples import (
    EmptyTicket,
    ExampleNotFound,
    Recording,
    TicketTooLong,
    list_names,
    select_example,
)
from jevlab.domain.triage import OriginMode, TriageResult
from jevlab.entrypoints.cli import triage_view
from jevlab.ports.environment import LocalEnvironment
from jevlab.ports.judge import JudgePort
from jevlab.ports.providers import GeneratorProbe, ModelCatalog
from jevlab.ports.recordings import RecordingLibrary
from jevlab.ports.specs import SpecLoader

app = typer.Typer(
    help="Laboratorio de Jev (TypeSafe).",
    no_args_is_help=True,
    add_completion=False,
)

_TAGS = {CheckStatus.OK: "[ok]", CheckStatus.FAIL: "[fail]", CheckStatus.UNAVAILABLE: "[n/d]"}
_TAG_WIDTH = 7
_NAME_WIDTH = 16


def configure_output_encoding() -> None:
    """UTF-8 en stdout y stderr también por una tubería de Windows (research.md R7, cli-ux.md)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


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
    configure_output_encoding()
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


# Errores de triaje -> código de salida (contracts/cli-triage.md, docs/standards/cli-ux.md §4).
_USAGE_ERRORS = (EmptyTicket, TicketTooLong, ExampleNotFound)
_SERVICE_ERRORS = (MissingApiKey, ProviderUnavailable, InvalidProviderResponse, RecordingOutdated)
_MENU_PREVIEW = 50
_LOG = logging.getLogger("jevlab")
_SLUG = {"sí": "si", "abstención": "abstencion"}
_NO_CHOICE = "sin triaje: no se eligió ningún ejemplo"


def build_spec_loader() -> SpecLoader:
    return YamlSpecLoader()


def build_recordings() -> RecordingLibrary:
    return YamlRecordingLibrary()


def replay_judge(recording: Recording) -> AbstractContextManager[JudgePort]:
    return TypeSafeJudge.replay(recording)


def live_judge(api_key: str) -> AbstractContextManager[JudgePort]:
    """Un solo cliente por ejecución, con reintentos por defecto y timeout de 10 s (R6)."""
    return TypeSafeJudge.live(api_key)


def is_terminal(stream: TextIO) -> bool:
    """En Windows, `isatty()` también es cierto para `NUL`; solo una consola tiene modo de consola."""
    if not stream.isatty():
        return False
    if sys.platform != "win32":
        return True
    import ctypes
    import msvcrt

    handle = msvcrt.get_osfhandle(stream.fileno())
    mode = ctypes.c_ulong()
    return bool(ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)))


def stdin_is_terminal() -> bool:
    return is_terminal(sys.stdin)


def _fail(message: str, code: int) -> typer.Exit:
    typer.echo(f"error: {message}", err=True)
    return typer.Exit(code)


def _choose(recordings: list[Recording]) -> Recording:
    """Menú numerado con el nombre y el inicio del texto de cada ejemplo (research.md R9)."""
    if not stdin_is_terminal():
        names = list_names([r.name for r in recordings])
        raise _fail(f"falta TEXTO o --ejemplo; ejemplos: {names}", 2)
    for number, recording in enumerate(recordings, start=1):
        text = recording.text
        preview = text if len(text) <= _MENU_PREVIEW else text[:_MENU_PREVIEW].rstrip() + "…"
        typer.echo(f"{number}. {recording.name}  {preview}")
    try:
        answer = typer.prompt("Elige un ejemplo", default="", show_default=False)
    except (typer.Abort, KeyboardInterrupt):
        answer = ""
    if not answer.strip().isdigit() or not 1 <= int(answer) <= len(recordings):
        typer.echo(_NO_CHOICE, err=True)
        raise typer.Exit(1)
    return recordings[int(answer) - 1]


def _log_result(result: TriageResult) -> None:
    """Solo metadatos y resultados interpretados (docs/standards/security.md §0 y §2)."""
    origin, priority = result.origin, result.priority
    queue = result.queue.assigned or "abstencion"
    urgency = _SLUG.get(str(result.urgency.verdict), str(result.urgency.verdict))
    threshold = {True: "si", False: "no", None: "-"}[priority.reaches_threshold]
    _LOG.info(
        "triage modo=%s ejemplo=%s modelo=%s cola=%s urgencia=%s prioridad=%s umbral=%s",
        _mode(en_vivo=origin.mode is OriginMode.EN_VIVO),
        origin.example or "-",
        origin.model,
        queue,
        urgency,
        priority.most_likely or "abstencion",
        threshold,
    )


def _mode(en_vivo: bool) -> str:
    return "en-vivo" if en_vivo else "grabado"


def _run(texto: str | None, ejemplo: str | None, en_vivo: bool) -> TriageResult:
    specs = build_spec_loader()
    if en_vivo:
        api_key = ProviderSettings().typesafe_api_key.strip()
        if not api_key:
            raise MissingApiKey()
        assert texto is not None
        with live_judge(api_key) as judge:
            return TriageTicket(judge=judge, specs=specs).run_live(texto)
    if texto is not None and not texto.strip():
        raise EmptyTicket()
    recordings = build_recordings().all()
    if texto is None and ejemplo is None:
        recording = _choose(recordings)
    else:
        recording = select_example(recordings, name=ejemplo, text=texto)
    with replay_judge(recording) as judge:
        return TriageTicket(judge=judge, specs=specs).run_recorded(recording)


@app.command()
def triage(
    texto: Annotated[
        str | None, typer.Argument(help="Texto del ticket.", show_default=False)
    ] = None,
    ejemplo: Annotated[
        str | None,
        typer.Option("--ejemplo", help="Nombre del ejemplo grabado.", show_default=False),
    ] = None,
    en_vivo: Annotated[
        bool, typer.Option("--en-vivo", help="Llama a TypeSafe con la clave de .env.")
    ] = False,
) -> None:
    """Clasifica un ticket de soporte con Choice, Noul y Score; por defecto, desde grabaciones."""
    if texto is not None and ejemplo is not None:
        raise _fail("TEXTO y --ejemplo son excluyentes", 2)
    if en_vivo and (texto is None or ejemplo is not None):
        raise _fail("--en-vivo necesita TEXTO y no admite --ejemplo", 2)
    try:
        result = _run(texto, ejemplo, en_vivo)
    except (*_USAGE_ERRORS, *_SERVICE_ERRORS, ProviderRejected) as error:
        _LOG.info("triage modo=%s error=%s", _mode(en_vivo), type(error).__name__)
        if isinstance(error, _USAGE_ERRORS):
            raise _fail(str(error), 2) from None
        if isinstance(error, ProviderRejected):
            raise _fail(f"TypeSafe rechazó la petición ({error.status})", 1) from None
        raise _fail(str(error), 1) from None
    _log_result(result)
    for line in triage_view.render(result):
        typer.echo(line)
