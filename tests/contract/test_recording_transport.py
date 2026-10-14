"""Contrato de RecordingTransport y ReplayTransport sobre httpx2 (research.md R5).

Las respuestas del transporte interno son sintéticas.
"""

import json

import httpx2
import pytest

from jevlab.adapters.recording_transport import RecordingTransport, ReplayTransport
from jevlab.domain.diagnostics import RecordingOutdated
from tests.builders import recording

_BODY = {"model": "jev-1.13.0", "answers": {}, "origen": "sintetico"}


def _inner(request: httpx2.Request) -> httpx2.Response:
    return httpx2.Response(200, json=_BODY, headers={"x-request-id": "sintetico"})


def test_records_bodies_without_any_header() -> None:
    transport = RecordingTransport(httpx2.MockTransport(_inner))
    with httpx2.Client(transport=transport) as client:
        response = client.post(
            "https://api.typesafe.ai/v1/systemone",
            json={"state": "hola", "model": "jev-1.13.0"},
            headers={"authorization": "Bearer clave-sintetica"},
        )

    assert response.json() == _BODY
    exchange = transport.last_exchange()
    assert exchange is not None
    assert exchange.request == {"state": "hola", "model": "jev-1.13.0"}
    assert exchange.response.status == 200
    assert exchange.response.body == _BODY
    dumped = json.dumps(exchange.model_dump(mode="json"))
    assert "authorization" not in dumped.lower()
    assert "clave-sintetica" not in dumped
    assert "x-request-id" not in dumped


def test_replays_the_recorded_response() -> None:
    recorded = recording(text="hola").model_copy(
        update={
            "request": {"state": "hola", "model": "jev-1.13.0"},
            "response": recording().response.model_copy(update={"body": _BODY}),
        }
    )
    with httpx2.Client(transport=ReplayTransport(recorded)) as client:
        # Mismo cuerpo con otro orden de claves: JSON canónico.
        response = client.post(
            "https://api.typesafe.ai/v1/systemone",
            content=json.dumps({"model": "jev-1.13.0", "state": "hola"}),
        )

    assert response.status_code == 200
    assert response.json() == _BODY


def test_different_body_is_an_outdated_recording() -> None:
    recorded = recording().model_copy(update={"request": {"state": "hola"}})
    with (
        httpx2.Client(transport=ReplayTransport(recorded)) as client,
        pytest.raises(RecordingOutdated) as error,
    ):
        client.post("https://api.typesafe.ai/v1/systemone", json={"state": "adiós"})

    assert error.value.name == "cobro-duplicado"
