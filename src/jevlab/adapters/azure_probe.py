"""Adaptador que comprueba el deployment de Azure OpenAI con una llamada mínima (research.md R2).

No conserva el contenido de la respuesta: solo importa si hubo error.
"""

import httpx2
from openai import APIConnectionError, APIStatusError, AzureOpenAI, OpenAIError

from jevlab.domain.diagnostics import ProviderRejected, ProviderUnavailable

_TIMEOUT_S = 20.0
_PING = [{"role": "user", "content": "Responde solo: ok"}]


class AzureGeneratorProbe:
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment: str,
        api_version: str,
        transport: httpx2.BaseTransport | None = None,
        max_retries: int = 1,
    ) -> None:
        self._endpoint = endpoint
        self._api_key = api_key
        self._deployment = deployment
        self._api_version = api_version
        self._transport = transport
        self._max_retries = max_retries

    def ping(self) -> None:
        config = (self._endpoint, self._api_key, self._deployment, self._api_version)
        if not all(value.strip() for value in config):
            raise ProviderRejected(None)
        http_client = httpx2.Client(transport=self._transport, timeout=_TIMEOUT_S)
        try:
            with AzureOpenAI(
                azure_endpoint=self._endpoint,
                api_key=self._api_key,
                api_version=self._api_version,
                max_retries=self._max_retries,
                timeout=_TIMEOUT_S,
                http_client=http_client,
            ) as client:
                client.chat.completions.create(
                    model=self._deployment,
                    messages=_PING,  # type: ignore[arg-type]
                    max_completion_tokens=16,
                )
        except APIConnectionError as error:
            raise ProviderUnavailable("sin conexión con Azure OpenAI") from error
        except APIStatusError as error:
            if error.status_code >= 500:
                raise ProviderUnavailable(f"Azure responde {error.status_code}") from error
            raise ProviderRejected(error.status_code) from error
        except OpenAIError as error:
            raise ProviderRejected(None) from error
