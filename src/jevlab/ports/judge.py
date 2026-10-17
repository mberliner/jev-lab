"""Puerto del juez: pregunta a Jev por un ticket con las decisiones de una petición.

Los adaptadores traducen los errores de su SDK a `ProviderUnavailable`, `ProviderRejected`,
`InvalidProviderResponse` o `RecordingOutdated`.
"""

from typing import Protocol

from jevlab.domain.decision_spec import ResolvedRequest
from jevlab.domain.examples import Exchange
from jevlab.domain.triage import Answers


class JudgePort(Protocol):
    def ask(self, request: ResolvedRequest, ticket: str) -> Answers: ...

    def last_exchange(self) -> Exchange | None:
        """Petición y respuesta de la última llamada, sin cabeceras; `None` si no se graba."""
        ...
