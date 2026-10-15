"""Tests para SingletonClient usando mocks del cargador,
la conexión y el escritor."""

import json
import socket
import threading
from unittest.mock import Mock, call

import pytest

from SingletonClient.app.exceptions import (
    ConnectionLostError,
    InvalidRequestError,
)
from SingletonClient.app.request_loader import RequestLoader
from SingletonClient.app.response_writer import ResponseWriter
from SingletonClient.app.server_connection import ServerConnection
from SingletonClient.app.singleton_client import SingletonClient

INPUT_PATH = "peticion.json"
REQUEST = {"UUID": "uuid-cpu", "ACTION": "get", "ID": "dato-1"}
RESPONSE = {"resultado": "correcto"}


@pytest.fixture
def loader():
    """Cargador simulado, sin llamadas reales a archivos."""
    return Mock(spec=RequestLoader)


@pytest.fixture
def connection():
    """Conexión simulada, sin llamadas reales a la red."""
    return Mock(spec=ServerConnection)


@pytest.fixture
def writer():
    """Escritor simulado, sin llamadas reales de salida."""
    return Mock(spec=ResponseWriter)


@pytest.fixture
def client(loader, connection, writer):
    """Cliente de prueba con las tres dependencias simuladas."""
    return SingletonClient(loader, connection, writer)


@pytest.fixture
def order(loader, connection, writer):
    """Mock padre para verificar el orden de las llamadas entre objetos."""
    order = Mock()
    order.attach_mock(loader.load, "load")
    order.attach_mock(connection.connect, "connect")
    order.attach_mock(connection.send, "send")
    order.attach_mock(connection.receive, "receive")
    order.attach_mock(connection.close, "close")
    order.attach_mock(writer.write, "write")
    return order


class TestInit:
    """Tests del constructor."""

    def test_guarda_las_dependencias(self, loader, connection, writer):
        client = SingletonClient(loader, connection, writer)
        assert client._loader is loader
        assert client._connection is connection
        assert client._writer is writer

    def test_no_realiza_operaciones(self, loader, connection, writer):
        SingletonClient(loader, connection, writer)
        loader.load.assert_not_called()
        connection.connect.assert_not_called()
        writer.write.assert_not_called()


class TestExecuteCaminoFeliz:
    """Tests del camino feliz de cada acción."""

    @pytest.mark.parametrize(
        "peticion,response",
        [
            (
                {"UUID": "u", "ACTION": "get", "ID": "dato-1"},
                {"ACTION": "ok", "VALUE": {}},
            ),
            (
                {"UUID": "u", "ACTION": "set", "ID": "dato-1", "web": "w"},
                {"ACTION": "ok"},
            ),
            (
                {"UUID": "u", "ACTION": "list"},
                [{"id": "dato-1"}, {"id": "dato-2"}],
            ),
        ],
    )
    def test_envia_la_peticion_escribe_y_retorna_la_respuesta(
        self, loader, connection, writer, client, peticion, response
    ):
        loader.load.return_value = peticion
        connection.receive.return_value = response

        result = client.execute(INPUT_PATH)

        loader.load.assert_called_once_with(INPUT_PATH)
        connection.send.assert_called_once_with(peticion)
        writer.write.assert_called_once_with(response)
        assert result == response

    def test_cierra_la_conexion(self, loader, connection, client):
        loader.load.return_value = REQUEST
        connection.receive.return_value = RESPONSE

        client.execute(INPUT_PATH)

        connection.close.assert_called_once()

    def test_llamadas_en_el_orden_esperado(
        self, loader, connection, client, order
    ):
        loader.load.return_value = REQUEST
        connection.receive.return_value = RESPONSE

        client.execute(INPUT_PATH)

        assert order.mock_calls == [
            call.load(INPUT_PATH),
            call.connect(),
            call.send(REQUEST),
            call.receive(),
            call.close(),
            call.write(RESPONSE),
        ]


class TestExecuteErrores:
    """Tests de propagación de excepciones."""

    def test_archivo_invalido_no_conecta(
        self, loader, connection, writer, client
    ):
        loader.load.side_effect = InvalidRequestError(
            "Falta el campo 'ACTION'."
        )

        with pytest.raises(InvalidRequestError):
            client.execute(INPUT_PATH)

        connection.connect.assert_not_called()
        connection.close.assert_not_called()
        writer.write.assert_not_called()

    def test_servidor_caido_en_connect(
        self, loader, connection, writer, client
    ):
        loader.load.return_value = REQUEST
        connection.connect.side_effect = ConnectionLostError(
            "No se pudo conectar"
        )

        with pytest.raises(ConnectionLostError):
            client.execute(INPUT_PATH)

        writer.write.assert_not_called()
        connection.close.assert_not_called()

    def test_falla_la_recepcion_y_cierra_la_conexion(
        self, loader, connection, writer, client
    ):
        loader.load.return_value = REQUEST
        connection.receive.side_effect = ConnectionLostError(
            "El servidor cerró la conexión"
        )

        with pytest.raises(ConnectionLostError):
            client.execute(INPUT_PATH)

        connection.close.assert_called_once()
        writer.write.assert_not_called()

    def test_respuesta_de_error_del_servidor_se_muestra_y_retorna(
        self, loader, connection, writer, client
    ):
        loader.load.return_value = REQUEST
        connection.receive.return_value = "Error"

        result = client.execute(INPUT_PATH)

        writer.write.assert_called_once_with("Error")
        assert result == "Error"


class TestIntegracion:
    """Prueba de integración contra un servidor de prueba real."""

    def test_envia_la_peticion_y_recibe_la_respuesta(self, tmp_path):
        input_path = tmp_path / "peticion.json"
        input_path.write_text(
            json.dumps({"ACTION": "get", "ID": "dato-1"}), encoding="utf-8"
        )

        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.bind(("127.0.0.1", 0))
        servidor.listen(1)
        host, port = servidor.getsockname()
        recibido = {}

        def handler():
            connexion, _ = servidor.accept()
            with connexion:
                reader = connexion.makefile("rb")
                recibido.update(json.loads(reader.readline().decode("utf-8")))
                connexion.sendall(
                    b'{"ACTION": "ok", "VALUE": {"ID": "dato-1"}}\n'
                )
                reader.close()
            servidor.close()

        hilo = threading.Thread(target=handler, daemon=True)
        hilo.start()

        writer = Mock(spec=ResponseWriter)
        client = SingletonClient(
            RequestLoader("uuid-cpu"),
            ServerConnection(host, port),
            writer,
        )

        response = client.execute(str(input_path))

        hilo.join(timeout=2)
        assert recibido == {
            "UUID": "uuid-cpu",
            "ACTION": "get",
            "ID": "dato-1",
        }
        assert response == {"ACTION": "ok", "VALUE": {"ID": "dato-1"}}
        writer.write.assert_called_once_with(response)
