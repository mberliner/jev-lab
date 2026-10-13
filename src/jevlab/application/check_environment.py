"""Caso de uso de `jevlab doctor`: comprueba el entorno y, si se pide, los proveedores.

Los textos de `detail` y `fix` siguen docs/standards/writing.md: español con tildes,
sin emojis ni pictogramas (specs/000-cimientos/contracts/cli-doctor.md).
"""

from jevlab.domain.diagnostics import (
    CheckResult,
    CheckStatus,
    DoctorReport,
    ProviderRejected,
    ProviderUnavailable,
    Scope,
)
from jevlab.ports.environment import LocalEnvironment, PythonInfo
from jevlab.ports.providers import GeneratorProbe, ModelCatalog

MIN_SPECKIT_PYTHON = (3, 8)
PROJECT_PYTHON = (3, 13)
DOCUMENTED_MODEL_ALIASES = frozenset({"jev-latest", "jev-preview"})

_RETRY_REMOTE = "comprueba la red y vuelve a ejecutar con --remote"


def _version(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


class CheckEnvironment:
    def __init__(
        self, local: LocalEnvironment, catalog: ModelCatalog, generator: GeneratorProbe
    ) -> None:
        self._local = local
        self._catalog = catalog
        self._generator = generator

    def run(self, remote: bool) -> DoctorReport:
        results = [self._speckit_python(), self._project_python(), self._env_keys()]
        if remote:
            results += [self._typesafe(), self._azure()]
        return DoctorReport(results=tuple(results), remote_requested=remote)

    def _speckit_python(self) -> CheckResult:
        info = self._local.speckit_python()
        name = "speckit-python"
        if info.version is None:
            return _fail(
                name,
                Scope.LOCAL,
                f"no se encuentra {info.executable}",
                "instala Python >= 3.8 como python3; en Windows crea el enlace python3.exe "
                "(docs/setup.md, apartado 3)",
            )
        if info.version[:2] < MIN_SPECKIT_PYTHON:
            return _fail(
                name,
                Scope.LOCAL,
                f"python3 {_version(info.version)} es anterior a 3.8",
                "instala Python >= 3.8 como python3 (docs/setup.md)",
            )
        if info.yaml_version is None:
            return _fail(
                name,
                Scope.LOCAL,
                f"python3 {_version(info.version)} sin PyYAML",
                "instala PyYAML en python3 o define SPECKIT_PYTHON_EXECUTABLE "
                "(docs/setup.md, apartado 4)",
            )
        return _ok(name, Scope.LOCAL, _speckit_detail(info))

    def _project_python(self) -> CheckResult:
        version = self._local.project_python()
        detail = f"Python {_version(version)}"
        if version[:2] != PROJECT_PYTHON:
            return _fail(
                "project-python",
                Scope.LOCAL,
                f"{detail}; se esperaba 3.13",
                "ejecuta uv sync en la raíz del repositorio y usa uv run jevlab",
            )
        return _ok("project-python", Scope.LOCAL, detail)

    def _env_keys(self) -> CheckResult:
        missing = self._local.missing_env_keys()
        if missing:
            return _fail(
                "env-keys",
                Scope.LOCAL,
                "faltan: " + ", ".join(missing),
                "copia .env.example a .env y rellena las variables que faltan",
            )
        return _ok("env-keys", Scope.LOCAL, "todas las variables de .env.example tienen valor")

    def _typesafe(self) -> CheckResult:
        name = "typesafe"
        try:
            models = self._catalog.list_models()
        except ProviderUnavailable as error:
            return _unavailable(name, error)
        except ProviderRejected as error:
            return _fail(name, Scope.REMOTE, *_typesafe_rejection(error.status))
        default = self._catalog.default_model()
        if not models:
            return _fail(
                name,
                Scope.REMOTE,
                "la clave no tiene modelos disponibles",
                "revisa la cuenta de TypeSafe asociada a TYPESAFE_API_KEY",
            )
        listed = ", ".join(models)
        if default not in models and default not in DOCUMENTED_MODEL_ALIASES:
            return _fail(
                name,
                Scope.REMOTE,
                f"el modelo por defecto {default} no está disponible; modelos: {listed}",
                "pon en TYPESAFE_DEFAULT_MODEL un modelo de la lista o jev-latest",
            )
        return _ok(name, Scope.REMOTE, f"modelos: {listed} (por defecto: {default})")

    def _azure(self) -> CheckResult:
        name = "azure"
        try:
            self._generator.ping()
        except ProviderUnavailable as error:
            return _unavailable(name, error)
        except ProviderRejected as error:
            return _fail(name, Scope.REMOTE, *_azure_rejection(error.status))
        return _ok(name, Scope.REMOTE, "el deployment responde")


def _speckit_detail(info: PythonInfo) -> str:
    assert info.version is not None
    detail = f"python3 {_version(info.version)} con PyYAML {info.yaml_version}"
    if info.yaml_via_override:
        detail += " (vía SPECKIT_PYTHON_EXECUTABLE)"
    return detail


def _typesafe_rejection(status: int | None) -> tuple[str, str]:
    if status is None:
        return "falta la clave", "define TYPESAFE_API_KEY en .env"
    if status in (401, 403):
        return f"clave rechazada (código {status})", "revisa TYPESAFE_API_KEY en .env"
    if status == 404:
        return "modelo o recurso inexistente (código 404)", "revisa TYPESAFE_DEFAULT_MODEL en .env"
    return f"petición rechazada (código {status})", "revisa la configuración de TypeSafe en .env"


def _azure_rejection(status: int | None) -> tuple[str, str]:
    if status is None:
        return (
            "configuración incompleta",
            (
                "define AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT y "
                "AZURE_OPENAI_API_VERSION en .env"
            ),
        )
    if status in (401, 403):
        return f"clave rechazada (código {status})", "revisa AZURE_OPENAI_API_KEY en .env"
    if status == 404:
        return (
            "deployment no encontrado (código 404)",
            "revisa AZURE_OPENAI_DEPLOYMENT y AZURE_OPENAI_API_VERSION en .env",
        )
    return (
        f"petición rechazada (código {status})",
        "revisa AZURE_OPENAI_ENDPOINT y AZURE_OPENAI_API_VERSION en .env",
    )


def _ok(name: str, scope: Scope, detail: str) -> CheckResult:
    return CheckResult(name=name, scope=scope, status=CheckStatus.OK, detail=detail)


def _fail(name: str, scope: Scope, detail: str, fix: str) -> CheckResult:
    return CheckResult(name=name, scope=scope, status=CheckStatus.FAIL, detail=detail, fix=fix)


def _unavailable(name: str, error: ProviderUnavailable) -> CheckResult:
    return CheckResult(
        name=name,
        scope=Scope.REMOTE,
        status=CheckStatus.UNAVAILABLE,
        detail=f"no disponible: {error.reason}",
        fix=_RETRY_REMOTE,
    )
