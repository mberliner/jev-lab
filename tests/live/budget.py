"""Tope de coste de los tests `live` (docs/standards/testing.md §6)."""

DEFAULT_BUDGET_USD = 0.10


def parse_budget(raw: str | None) -> float:
    """Lee `JEVLAB_LIVE_BUDGET_USD`; sin valor, el tope por defecto."""
    if raw is None or not raw.strip():
        return DEFAULT_BUDGET_USD
    budget = float(raw)
    if budget < 0:
        raise ValueError("JEVLAB_LIVE_BUDGET_USD no puede ser negativo")
    return budget


def check_budget(caps: dict[str, float | None], budget: float) -> str | None:
    """Devuelve el motivo para abortar la sesión, o None si los topes caben en el presupuesto."""
    undeclared = sorted(name for name, cap in caps.items() if cap is None)
    if undeclared:
        return "tests live sin max_usd: " + ", ".join(undeclared)
    total = sum(cap for cap in caps.values() if cap is not None)
    if total > budget:
        return (
            f"los tests live seleccionados suman {total:g} USD y superan "
            f"JEVLAB_LIVE_BUDGET_USD={budget:g}"
        )
    return None
