"""La suite por defecto se ejecuta con la red bloqueada (docs/standards/testing.md §3)."""

import socket

import pytest
from pytest_socket import SocketBlockedError


@pytest.mark.filterwarnings("ignore:A test tried to use socket.socket")
def test_opening_a_tcp_socket_is_blocked() -> None:
    with pytest.raises(SocketBlockedError):
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)
