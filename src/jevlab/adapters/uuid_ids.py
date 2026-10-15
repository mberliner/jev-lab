"""Identificadores de petición con `uuid4` (research.md R6)."""

import uuid


class UuidIdGenerator:
    def new_request_id(self) -> str:
        return str(uuid.uuid4())
