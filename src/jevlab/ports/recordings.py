"""Puerto de la biblioteca de ejemplos grabados (contracts/recording.md)."""

from typing import Protocol

from jevlab.domain.examples import Recording


class RecordingLibrary(Protocol):
    def all(self) -> list[Recording]:
        """Todas las grabaciones, ordenadas por nombre."""
        ...

    def save(self, recording: Recording) -> None: ...
