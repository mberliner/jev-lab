"""Puerta de instrucciones: `CLAUDE.md` solo importa `AGENTS.md` (ADR-0002, research.md R11)."""

from pathlib import Path

from checks._common import report, root_parser

EXPECTED = ["@AGENTS.md"]


def check_agents(root: Path) -> list[str]:
    path = root / "CLAUDE.md"
    if not path.is_file():
        return ["CLAUDE.md: ADR-0002 (fuente única): falta CLAUDE.md con solo @AGENTS.md"]
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    if [line for line in lines if line] != EXPECTED:
        return [
            (
                "CLAUDE.md: ADR-0002 (fuente única): debe contener solo @AGENTS.md; "
                "las instrucciones van en AGENTS.md"
            )
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    args = root_parser(__doc__ or "").parse_args(argv)
    return report(check_agents(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
