"""Puerta de portabilidad: sin rutas absolutas de máquina ni enlaces simbólicos (Constitución VI).

Los patrones son genéricos; la ruta absoluta del propio repositorio se calcula al ejecutarse.
"""

import re
from pathlib import Path

from checks._common import git, repo_files, report, root_parser

# Una ruta de máquina empieza un token: no va precedida de un dominio ni de otra ruta (URLs).
_START = r"(?<![\w.\-/\\:])"
_NAME = r"[\w.\-]+"
_MACHINE_PATHS = (
    _START + r"/(?:home|Users)/" + _NAME + "/",
    _START + r"/(?:root)/" + _NAME,
    r"(?<![\w])[A-Za-z]:\\(?:Users)\\" + _NAME,
)
_SYMLINK_MODE = "120000"


def _patterns(root: Path) -> re.Pattern[str]:
    resolved = root.resolve()
    own = {re.escape(str(resolved)), re.escape(resolved.as_posix())}
    return re.compile("|".join([*_MACHINE_PATHS, *sorted(own)]), re.IGNORECASE)


def _symlinks_in_index(root: Path) -> set[str]:
    links = set()
    for line in git(root, "ls-files", "-s", "-z").split("\0"):
        if line.startswith(_SYMLINK_MODE + " "):
            links.add(line.split("\t", 1)[1])
    return links


def check_paths(root: Path) -> list[str]:
    pattern = _patterns(root)
    links = _symlinks_in_index(root)
    errors = [f"{name}: Constitución VI (sin enlaces simbólicos)" for name in sorted(links)]
    for name in repo_files(root):
        path = root / name
        if name in links:
            continue
        if path.is_symlink():
            errors.append(f"{name}: Constitución VI (sin enlaces simbólicos)")
            continue
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if match := pattern.search(line):
                errors.append(
                    f"{name}:{number}: Constitución VI (sin rutas absolutas de máquina): "
                    f"«{match.group()}»; usa una ruta relativa"
                )
    return errors


def main(argv: list[str] | None = None) -> int:
    args = root_parser(__doc__ or "").parse_args(argv)
    return report(check_paths(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
