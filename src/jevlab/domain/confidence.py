"""Fórmulas oficiales de la confianza (https://docs.typesafe.ai/confidence.md, research.md R3).

Noul no tiene confianza: la salida muestra su probabilidad y la banda, sin inventarla.
Las probabilidades se usan tal como llegan, sin normalizar.
"""

from collections.abc import Mapping, Sequence


def choice_confidence(probabilities: Mapping[str, float]) -> float:
    """`(p_max - 1/n) / (1 - 1/n)`, con `n` opciones (escape incluido), sin recortar."""
    n = len(probabilities)
    if n < 2:
        raise ValueError("la confianza de Choice necesita al menos dos opciones")
    uniform = 1 / n
    return (max(probabilities.values()) - uniform) / (1 - uniform)


def most_likely_position(probabilities: Sequence[float]) -> int:
    """Posición más probable; un empate se resuelve con la primera (decisión propia, R3)."""
    return max(range(len(probabilities)), key=lambda i: (probabilities[i], -i))


def score_confidence(probabilities: Sequence[float]) -> float:
    """`max(0, 1 - Σ p_i · |i - m| / MAD_unif)`, con `MAD_unif = (1/n) · Σ |i - (n-1)/2|`."""
    n = len(probabilities)
    if n < 2:
        raise ValueError("la confianza de Score necesita al menos dos niveles")
    m = most_likely_position(probabilities)
    mad_uniform = sum(abs(i - (n - 1) / 2) for i in range(n)) / n
    spread = sum(p * abs(i - m) for i, p in enumerate(probabilities))
    return max(0.0, 1 - spread / mad_uniform)
