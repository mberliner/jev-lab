"""Puerto de identificadores: el único origen de IDs fuera de los adaptadores (research R6)."""

from typing import Protocol


class IdGenerator(Protocol):
    def new_request_id(self) -> str: ...
