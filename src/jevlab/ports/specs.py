"""Puerto que carga y valida una definición de petición con sus decisiones."""

from typing import Protocol

from jevlab.domain.decision_spec import ResolvedRequest


class SpecLoader(Protocol):
    def load_request(self, name: str) -> ResolvedRequest: ...
