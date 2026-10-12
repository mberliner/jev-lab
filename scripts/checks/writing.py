"""Puerta de redacción: docs/standards/writing.md §1 y §2 en los archivos Markdown."""

import re
from pathlib import Path

from checks._common import repo_files, report, root_parser

EXCLUDED_PREFIXES = (".specify/templates/", ".claude/skills/", ".agents/skills/")
EXCLUDED_FILES = frozenset({"docs/standards/writing.md"})

_EMOJI = re.compile(
    "["
    "\U0001f000-\U0001faff"  # emojis y pictogramas
    "☀-➿"  # símbolos varios y dingbats
    "⬀-⯿"  # flechas y estrellas suplementarias
    "⌚⌛⏩-⏺"  # relojes y controles
    "️"  # selector de variante emoji
    "]"
)
_DIAGRAM = re.compile(
    "["
    "─-╿"  # dibujo de cajas
    "←-⇿"  # flechas
    "■-◿"  # formas geométricas, incluidos los triángulos
    "]"
)
_FENCE = re.compile(r"^\s{0,3}(?:\s*)(`{3,}|~{3,})")


def check_text(name: str, text: str) -> list[str]:
    errors = []
    fence: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        match = _FENCE.match(line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
        if found := _EMOJI.search(line):
            errors.append(
                f"{name}:{number}: writing.md §1 (emoji o pictograma): "
                f"U+{ord(found.group()):04X}; escribe una palabra"
            )
        elif fence is None and (found := _DIAGRAM.search(line)):
            errors.append(
                f"{name}:{number}: writing.md §2 (caja o flecha fuera de bloque de código): "
                f"U+{ord(found.group()):04X}; usa palabras o ->"
            )
    return errors


def _checked(name: str) -> bool:
    return (
        name.endswith(".md")
        and name not in EXCLUDED_FILES
        and not name.startswith(EXCLUDED_PREFIXES)
    )


def check_repo(root: Path) -> list[str]:
    errors = []
    for name in repo_files(root):
        if _checked(name):
            errors += check_text(name, (root / name).read_text(encoding="utf-8"))
    return errors


def main(argv: list[str] | None = None) -> int:
    args = root_parser(__doc__ or "").parse_args(argv)
    return report(check_repo(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
