"""Puertos de los proveedores remotos.

Los adaptadores traducen los errores de su SDK a `ProviderUnavailable` y `ProviderRejected`.
"""

from typing import Protocol


class ModelCatalog(Protocol):
    def list_models(self) -> list[str]: ...

    def default_model(self) -> str: ...


class GeneratorProbe(Protocol):
    def ping(self) -> None: ...
