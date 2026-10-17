"""Puerto que carga y valida la política de enrutado (spec 002, research.md R3)."""

from pathlib import Path
from typing import Protocol

from jevlab.domain.policy import Policy


class PolicyLoader(Protocol):
    def load(self, path: Path | None) -> Policy:
        """La política del paquete con `None`, o la de ese archivo; si no vale, `InvalidPolicy`."""
        ...
