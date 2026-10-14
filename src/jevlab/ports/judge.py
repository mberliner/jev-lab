"""Puerto del juez: pregunta a Jev por un ticket con la definición de triaje.

Los adaptadores traducen los errores de su SDK a `ProviderUnavailable`, `ProviderRejected`,
`InvalidProviderResponse` o `RecordingOutdated`.
"""

from typing import Protocol

from jevlab.domain.decision_spec import TriageSpec
from jevlab.domain.examples import Exchange
from jevlab.domain.triage import TriageAnswers


class JudgePort(Protocol):
    def ask(self, spec: TriageSpec, ticket: str) -> TriageAnswers: ...

    def last_exchange(self) -> Exchange | None:
        """Petición y respuesta de la última llamada, sin cabeceras; `None` si no se graba."""
        ...
