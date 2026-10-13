"""Contrato de AzureGeneratorProbe con un transporte httpx2 simulado (research.md R2 y R3).

Todas las respuestas son sintéticas: imitan la forma de Chat Completions, no son grabaciones de
Azure OpenAI.
"""

import json
from collections.abc import Callable

import httpx2
import pytest

from jevlab.adapters.azure_probe import AzureGeneratorProbe
from jevlab.domain.diagnostics import ProviderRejected, ProviderUnavailable

Handler = Callable[[httpx2.Request], httpx2.Response]

_COMPLETION = {
    "id": "sintetico",
    "object": "chat.completion",
    "created": 0,
    "model": "sintetico",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "sintetico"},
            "finish_reason": "stop",
        }
    ],
}


def _probe(handler: Handler, api_key: str = "clave-de-prueba") -> AzureGeneratorProbe:
    return AzureGeneratorProbe(
        endpoint="https://recurso-de-prueba.openai.azure.com",
        api_key=api_key,
        deployment="despliegue",
        api_version="2024-10-21",
        transport=httpx2.MockTransport(handler),
        max_retries=0,
    )


def test_ping_sends_a_minimal_completion_to_the_deployment() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json=_COMPLETION)

    _probe(handler).ping()

    request = seen[0]
    assert request.url.path == "/openai/deployments/despliegue/chat/completions"
    assert request.url.params["api-version"] == "2024-10-21"
    body = json.loads(request.content)
    assert body["max_completion_tokens"] == 16
    assert len(body["messages"]) == 1


@pytest.mark.parametrize("status", [401, 403, 404])
def test_client_errors_are_rejections(status: int) -> None:
    probe = _probe(lambda r: httpx2.Response(status, json={"error": {"message": "sintetico"}}))
    with pytest.raises(ProviderRejected) as error:
        probe.ping()
    assert error.value.status == status


def test_server_error_is_unavailable() -> None:
    with pytest.raises(ProviderUnavailable):
        _probe(lambda r: httpx2.Response(500, json={"error": {"message": "sintetico"}})).ping()


def test_connection_error_is_unavailable() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("sin red", request=request)

    with pytest.raises(ProviderUnavailable):
        _probe(handler).ping()


def test_incomplete_configuration_is_a_rejection_without_status() -> None:
    with pytest.raises(ProviderRejected) as error:
        _probe(lambda r: httpx2.Response(200, json=_COMPLETION), api_key="").ping()
    assert error.value.status is None
