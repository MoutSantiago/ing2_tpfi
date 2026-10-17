"""Pruebas de la comunicación TCP de SingletonClient."""

import json
import socket
import threading

import pytest

from SingletonClient.app.exceptions import ConnectionLostError
from SingletonClient.app.server_connection import ServerConnection


def start_server(handler):
    """Inicia un servidor TCP local en un puerto libre."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    host, port = server.getsockname()

    def run():
        try:
            connection, _ = server.accept()
            with connection:
                handler(connection)
        finally:
            server.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    return host, port, thread


def test_connect_send_and_receive():
    """Envía y recibe una petición JSON completa."""
    expected = {"accion": "get", "clave": "nombre"}

    def handler(connection):
        reader = connection.makefile("rb")
        received = reader.readline()
        assert received.endswith(b"\n")
        assert json.loads(received.decode("utf-8")) == expected

        connection.sendall(b'{"resultado": "correcto"}\n')
        reader.close()

    host, port, thread = start_server(handler)
    client = ServerConnection(host, port)

    assert not client.is_open

    try:
        client.connect()
        assert client.is_open

        client.send(expected)
        response = client.receive()

        assert response == {"resultado": "correcto"}
    finally:
        client.close()

    thread.join(timeout=2)
    assert not client.is_open


def test_receive_list_and_text():
    """Interpreta correctamente listas y textos JSON."""
    responses = [
        (b'[{"id": 1}, {"id": 2}]\n', [{"id": 1}, {"id": 2}]),
        (b'"Error"\n', "Error"),
    ]

    for payload, expected in responses:

        def handler(connection, data=payload):
            connection.sendall(data)

        host, port, thread = start_server(handler)
        client = ServerConnection(host, port, read_timeout=1)

        try:
            client.connect()
            assert client.receive() == expected
        finally:
            client.close()

        thread.join(timeout=2)


def test_send_preserves_accents():
    """Los caracteres acentuados se transmiten en UTF-8."""
    message = {"nombre": "Concepción", "acción": "búsqueda"}

    def handler(connection):
        data = connection.makefile("rb").readline()
        assert data.endswith(b"\n")
        assert json.loads(data.decode("utf-8")) == message

    host, port, thread = start_server(handler)
    client = ServerConnection(host, port)

    try:
        client.connect()
        client.send(message)
    finally:
        client.close()

    thread.join(timeout=2)


def test_connect_to_unavailable_port():
    """La conexión a un puerto sin servidor genera ConnectionLostError."""
    with socket.socket() as temporary_socket:
        temporary_socket.bind(("127.0.0.1", 0))
        port = temporary_socket.getsockname()[1]

    client = ServerConnection("127.0.0.1", port)

    with pytest.raises(ConnectionLostError):
        client.connect()


def test_receive_without_connection():
    """No permite recibir si no hay conexión abierta."""
    client = ServerConnection("127.0.0.1", 12345)

    with pytest.raises(ConnectionLostError):
        client.receive()


def test_send_without_connection():
    """No permite enviar si no hay conexión abierta."""
    client = ServerConnection("127.0.0.1", 12345)

    with pytest.raises(ConnectionLostError):
        client.send({"accion": "list"})


def test_receive_invalid_json():
    """Un JSON inválido genera ValueError."""

    def handler(connection):
        connection.sendall(b"{no es json}\n")

    host, port, thread = start_server(handler)
    client = ServerConnection(host, port)

    try:
        client.connect()

        with pytest.raises(ValueError, match="JSON válido"):
            client.receive()

        # Un error de formato no cierra automáticamente la conexión.
        assert client.is_open
    finally:
        client.close()

    thread.join(timeout=2)


def test_receive_without_newline():
    """Una respuesta incompleta genera ConnectionLostError."""

    def handler(connection):
        connection.sendall(b'{"resultado":')
        # Al salir del handler, se cierra el socket.

    host, port, thread = start_server(handler)
    client = ServerConnection(host, port)

    try:
        client.connect()

        with pytest.raises(ConnectionLostError):
            client.receive()
    finally:
        client.close()

    thread.join(timeout=2)


def test_close_is_idempotent():
    """Cerrar dos veces no genera errores."""
    client = ServerConnection("127.0.0.1", 12345)

    client.close()
    client.close()

    assert not client.is_open
