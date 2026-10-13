"""Contrato de TypeSafeModelCatalog con un transporte httpx2 simulado (research.md R1 y R3).

Todas las respuestas son sintéticas: imitan la forma documentada de `GET /v1/models`, no son
grabaciones de TypeSafe.
"""

from collections.abc import Callable

import httpx2
import pytest

from jevlab.adapters.typesafe_catalog import TypeSafeModelCatalog
from jevlab.domain.diagnostics import ProviderRejected, ProviderUnavailable

Handler = Callable[[httpx2.Request], httpx2.Response]

_MODELS = {
    "origen": "sintetico",
    "models": [
        {"name": "jev-1.13", "description": "sintetico", "release_date": "2026-01-01"},
        {"name": "jev-latest", "description": "sintetico", "release_date": "2026-01-01"},
    ],
}


def _catalog(handler: Handler, api_key: str | None = "clave-de-prueba") -> TypeSafeModelCatalog:
    return TypeSafeModelCatalog(
        api_key=api_key, model="jev-1.13", transport=httpx2.MockTransport(handler), max_retries=0
    )


def test_lists_model_names_from_models_endpoint() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json=_MODELS)

    assert _catalog(handler).list_models() == ["jev-1.13", "jev-latest"]
    assert seen[0].method == "GET"
    assert seen[0].url.path == "/v1/models"


def test_default_model_is_the_configured_one() -> None:
    assert _catalog(lambda r: httpx2.Response(200, json=_MODELS)).default_model() == "jev-1.13"


def test_default_model_falls_back_to_sdk_default() -> None:
    catalog = TypeSafeModelCatalog(api_key="clave", model=None)
    assert catalog.default_model() == "jev-latest"


@pytest.mark.parametrize("status", [401, 403, 404])
def test_client_errors_are_rejections(status: int) -> None:
    catalog = _catalog(lambda r: httpx2.Response(status, json={"error": "sintetico"}))
    with pytest.raises(ProviderRejected) as error:
        catalog.list_models()
    assert error.value.status == status


def test_server_error_is_unavailable() -> None:
    with pytest.raises(ProviderUnavailable):
        _catalog(lambda r: httpx2.Response(503)).list_models()


def test_connection_error_is_unavailable() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("sin red", request=request)

    with pytest.raises(ProviderUnavailable):
        _catalog(handler).list_models()


def test_missing_key_is_a_rejection_without_status() -> None:
    with pytest.raises(ProviderRejected) as error:
        _catalog(lambda r: httpx2.Response(200, json=_MODELS), api_key="").list_models()
    assert error.value.status is None
