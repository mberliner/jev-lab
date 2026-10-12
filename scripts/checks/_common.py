"""Utilidades compartidas por las puertas: archivos del repositorio y argumentos comunes."""

import argparse
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout


def repo_files(root: Path) -> list[str]:
    """Archivos versionados y nuevos no ignorados, con rutas POSIX relativas a la raíz."""
    output = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    return sorted({name for name in output.split("\0") if name})


def root_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="raíz del repositorio")
    return parser


def report(errors: Iterable[str]) -> int:
    """Escribe los errores en stderr; devuelve el código de salida de la puerta."""
    found = list(errors)
    for error in found:
        print(error, file=sys.stderr)
    return 1 if found else 0
