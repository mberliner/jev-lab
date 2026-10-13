"""Puerta del mensaje de commit: docs/standards/version-control.md §1 y §2.

Uso: `commit_msg.py <archivo-del-mensaje>` (gancho `commit-msg`) o
`commit_msg.py --range <a>..<b>` (CI). Un rango sin `..`, o que empieza en el SHA nulo de un
push nuevo, comprueba toda la historia alcanzable. Los commits de merge se omiten.
"""

import re
from pathlib import Path

from checks._common import git, report, root_parser

TYPES = ("feat", "fix", "docs", "test", "refactor", "perf", "build", "ci", "chore")
_HEADER = re.compile(rf"^(?:{'|'.join(TYPES)})(?:\([^()\s]+\))?!?: \S")
_ATTRIBUTION = re.compile(r"^\s*co-authored-by:|generated with", re.IGNORECASE | re.MULTILINE)
_NULL_SHA = "0" * 40
_SUMMARY_LIMIT = 72


def check_message(text: str) -> list[str]:
    lines = [line for line in text.splitlines() if not line.startswith("#")]
    header = lines[0].strip() if lines else ""
    errors = []
    if not _HEADER.match(header):
        errors.append(
            f"version-control.md §1 (Conventional Commits): «{header}» no sigue "
            f"tipo(ámbito): resumen, con tipo en {', '.join(TYPES)}"
        )
    if _ATTRIBUTION.search("\n".join(lines)):
        errors.append(
            "version-control.md §2 (sin atribución de agentes): quita las líneas "
            "Co-Authored-By o Generated with"
        )
    return errors


def _revisions(spec: str) -> list[str]:
    start, sep, end = spec.partition("..")
    if not sep:
        return [spec]
    if not start or set(start) == {"0"} or start == _NULL_SHA:
        return [end or "HEAD"]
    return [f"{start}..{end or 'HEAD'}"]


def check_range(root: Path, spec: str) -> list[str]:
    output = git(root, "log", "--no-merges", "--format=%H%x00%B%x1e", *_revisions(spec))
    errors = []
    for entry in output.split("\x1e"):
        sha, _, body = entry.strip("\n").partition("\0")
        if sha:
            errors += [f"commit {sha[:7]}: {e}" for e in check_message(body)]
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = root_parser(__doc__ or "")
    parser.add_argument("message_file", nargs="?", type=Path)
    parser.add_argument("--range", dest="revision_range")
    args = parser.parse_args(argv)
    if args.revision_range:
        return report(check_range(args.root, args.revision_range))
    if args.message_file is None:
        parser.error("indica el archivo del mensaje o --range")
    text = args.message_file.read_text(encoding="utf-8")
    summary = next((line for line in text.splitlines() if not line.startswith("#")), "")
    if len(summary) > _SUMMARY_LIMIT:
        print(f"aviso: el resumen tiene {len(summary)} caracteres (recomendado: {_SUMMARY_LIMIT})")
    return report(check_message(text))


if __name__ == "__main__":
    raise SystemExit(main())
