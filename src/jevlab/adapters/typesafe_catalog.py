"""Adaptador del catálogo de modelos de TypeSafe (research.md R1)."""

import httpx2
from typesafe_sdk import (
    RetryPolicy,
    TypeSafeAPIConnectionError,
    TypeSafeAPIError,
    TypeSafeClient,
    TypeSafeError,
)
from typesafe_sdk.constants import DEFAULT_MODEL

from jevlab.domain.diagnostics import ProviderRejected, ProviderUnavailable

_TIMEOUT_S = 10.0


class TypeSafeModelCatalog:
    def __init__(
        self,
        api_key: str | None,
        model: str | None,
        transport: httpx2.BaseTransport | None = None,
        max_retries: int = 1,
    ) -> None:
        self._api_key = api_key
        self._model = model or DEFAULT_MODEL
        self._transport = transport
        self._max_retries = max_retries

    def default_model(self) -> str:
        return self._model

    def list_models(self) -> list[str]:
        try:
            with TypeSafeClient(
                api_key=self._api_key or "",
                model=self._model,
                retry=RetryPolicy(max_retries=self._max_retries),
                timeout=_TIMEOUT_S,
                transport=self._transport,
            ) as client:
                response = client.models.list()
        except TypeSafeAPIConnectionError as error:
            raise ProviderUnavailable("sin conexión con TypeSafe") from error
        except TypeSafeAPIError as error:
            if error.status >= 500:
                raise ProviderUnavailable(f"TypeSafe responde {error.status}") from error
            raise ProviderRejected(error.status) from error
        except TypeSafeError as error:
            raise ProviderRejected(None) from error
        return [model.name for model in response.models]
