"""Grabación y reproducción sobre el transporte de httpx2 (research.md R5).

No se guarda ninguna cabecera: ni la de autorización ni ninguna otra.
"""

import json
from typing import Any

import httpx2

from jevlab.domain.diagnostics import RecordingOutdated
from jevlab.domain.examples import Exchange, RecordedResponse, Recording


def canonical(body: Any) -> str:
    return json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class RecordingTransport(httpx2.BaseTransport):
    """Deja pasar la petición al transporte real y guarda el último intercambio."""

    def __init__(self, inner: httpx2.BaseTransport) -> None:
        self._inner = inner
        self._last: Exchange | None = None

    def handle_request(self, request: httpx2.Request) -> httpx2.Response:
        response = self._inner.handle_request(request)
        content = response.read()
        try:
            body = json.loads(content)
        except ValueError:
            body = None
        if isinstance(body, dict):
            self._last = Exchange(
                request=json.loads(request.read()),
                response=RecordedResponse(status=response.status_code, body=body),
            )
        else:
            self._last = None
        return response

    def last_exchange(self) -> Exchange | None:
        return self._last

    def close(self) -> None:
        self._inner.close()


class ReplayTransport(httpx2.BaseTransport):
    """Devuelve la respuesta grabada si la petición coincide con la grabada."""

    def __init__(self, recording: Recording) -> None:
        self._recording = recording

    def handle_request(self, request: httpx2.Request) -> httpx2.Response:
        if canonical(json.loads(request.read())) != canonical(self._recording.request):
            raise RecordingOutdated(self._recording.name)
        response = self._recording.response
        return httpx2.Response(response.status, json=response.body)
