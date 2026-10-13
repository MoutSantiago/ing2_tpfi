"""Tests para ObserverClient usando mocks de la conexión y del escritor."""

import logging
import threading
import time
import uuid
from unittest.mock import Mock, call

import pytest

from ObserverClient.app.exceptions import ConnectionLostError
from ObserverClient.app.observer_client import (
    DEFAULT_RETRY_INTERVAL,
    ObserverClient,
)


def build_scripted_connection(scripts):
    """Crea una conexión falsa que reproduce guiones de recepción.

    Cada elemento de scripts corresponde a un intento de conexión: una lista
    de resultados para receive(). Un resultado puede ser un mensaje a retornar
    o una excepción a lanzar. Cuando el guion del intento se agota, receive()
    lanza ConnectionLostError.
    """
    state = {"attempt": -1, "pending": []}
    connection = Mock()
    connection.sent = []

    def connect() -> None:
        state["attempt"] += 1
        state["pending"] = list(scripts[state["attempt"]])

    def receive():
        if not state["pending"]:
            raise ConnectionLostError("El servidor cerró la conexión")
        result = state["pending"].pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def send(message) -> None:
        connection.sent.append(message)

    connection.connect.side_effect = connect
    connection.receive.side_effect = receive
    connection.send.side_effect = send
    return connection


@pytest.fixture
def connection():
    """Conexión simulada, sin llamadas reales a la red."""
    return Mock()


@pytest.fixture
def writer():
    """Escritor simulado, sin llamadas reales de salida."""
    return Mock()


@pytest.fixture
def client(connection, writer):
    """Cliente de prueba con host, puerto e intervalo conocidos."""
    return ObserverClient(
        "localhost", 8080, connection, writer, retry_interval=5
    )


class TestInit:
    """Tests del constructor."""

    def test_guarda_los_datos_recibidos(self, connection, writer):
        client = ObserverClient("host", 1234, connection, writer)
        assert client._host == "host"
        assert client._port == 1234
        assert client._connection is connection
        assert client._writer is writer

    def test_intervalo_por_defecto(self, connection, writer):
        client = ObserverClient("host", 1234, connection, writer)
        assert client._retry_interval == DEFAULT_RETRY_INTERVAL
        assert DEFAULT_RETRY_INTERVAL == 30

    def test_intervalo_personalizado(self, connection, writer):
        client = ObserverClient(
            "host", 1234, connection, writer, retry_interval=7
        )
        assert client._retry_interval == 7

    def test_uuid_es_el_de_la_cpu(self, client):
        assert client._uuid == str(uuid.getnode())

    def test_stop_event_no_esta_activado_al_iniciar(self, client):
        assert isinstance(client._stop_event, threading.Event)
        assert not client._stop_event.is_set()

    def test_no_abre_la_conexion(self, connection, writer):
        ObserverClient("host", 1234, connection, writer)
        connection.connect.assert_not_called()

    @pytest.mark.parametrize("invalido", [0, -1, -30])
    def test_intervalo_no_positivo_lanza_value_error(
        self, connection, writer, invalido
    ):
        with pytest.raises(ValueError):
            ObserverClient(
                "host", 1234, connection, writer, retry_interval=invalido
            )


class TestBuildRequest:
    """Tests de la construcción de la solicitud de suscripción."""

    def test_incluye_uuid_y_accion(self, client):
        assert client._build_request() == {
            "uuid": client._uuid,
            "action": "subscribe",
        }

    def test_no_incluye_id(self, client):
        assert "id" not in client._build_request()


class TestSubscribe:
    """Tests del envío de la suscripción."""

    def test_envia_la_solicitud(self, client, connection):
        client._subscribe()
        connection.send.assert_called_once_with(
            {"uuid": client._uuid, "action": "subscribe"}
        )

    def test_propaga_connection_lost(self, client, connection):
        connection.send.side_effect = ConnectionLostError("falló el envío")
        with pytest.raises(ConnectionLostError):
            client._subscribe()


class TestStop:
    """Tests de la detención del programa."""

    def test_activa_el_evento_y_cierra_la_conexion(self, client, connection):
        client.stop()
        assert client._stop_event.is_set()
        connection.close.assert_called_once()

    def test_es_idempotente(self, client, connection):
        client.stop()
        client.stop()
        assert client._stop_event.is_set()
        connection.close.assert_called_once()


class TestListen:
    """Tests del bucle de escucha."""

    def test_entrega_cada_mensaje_al_writer(self, client, connection, writer):
        connection.receive.side_effect = [
            {"n": 1},
            {"n": 2},
            ConnectionLostError("corte"),
        ]
        with pytest.raises(ConnectionLostError):
            client._listen()
        assert writer.write.call_args_list == [
            call({"n": 1}),
            call({"n": 2}),
        ]

    def test_continua_tras_un_mensaje_invalido(
        self, client, connection, writer, caplog
    ):
        connection.receive.side_effect = [
            ValueError("no es JSON"),
            {"n": 1},
            ConnectionLostError("corte"),
        ]
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ConnectionLostError):
                client._listen()
        writer.write.assert_called_once_with({"n": 1})
        assert "inválido" in caplog.text

    def test_propaga_el_error_de_escritura(self, client, connection, writer):
        connection.receive.return_value = {"n": 1}
        writer.write.side_effect = OSError("disco lleno")
        with pytest.raises(OSError):
            client._listen()

    def test_sale_si_se_pidio_detener(self, client, connection):
        client._stop_event.set()
        client._listen()
        connection.receive.assert_not_called()


class TestWaitToRetry:
    """Tests de la espera entre reintentos."""

    def test_espera_el_intervalo(self, client):
        client._stop_event = Mock()
        client._wait_to_retry()
        client._stop_event.wait.assert_called_once_with(5)

    def test_se_interrumpe_si_se_pidio_detener(self, client):
        client._stop_event.set()
        inicio = time.monotonic()
        client._wait_to_retry()
        assert time.monotonic() - inicio < 1


class TestRun:
    """Tests del ciclo principal del cliente."""

    def test_retorna_de_inmediato_si_ya_se_pidio_detener(
        self, client, connection
    ):
        client._stop_event.set()
        client.run()
        connection.connect.assert_not_called()

    def test_camino_feliz_conecta_suscribe_y_escribe(
        self, connection, writer, monkeypatch
    ):
        scripted = build_scripted_connection([[{"n": 1}]])
        client = ObserverClient(
            "host", 8080, scripted, writer, retry_interval=1
        )
        monkeypatch.setattr(client, "_wait_to_retry", lambda: None)
        writer.write.side_effect = lambda _m: client.stop()

        client.run()

        assert scripted.connect.call_count == 1
        assert scripted.sent == [{"uuid": client._uuid, "action": "subscribe"}]
        assert writer.write.call_args_list == [call({"n": 1})]
        assert client._stop_event.is_set()

    def test_reintenta_tras_corte_y_reenvia_suscripcion(
        self, writer, monkeypatch
    ):
        scripted = build_scripted_connection([[], [{"n": 1}]])
        client = ObserverClient(
            "host", 8080, scripted, writer, retry_interval=1
        )
        monkeypatch.setattr(client, "_wait_to_retry", lambda: None)
        writer.write.side_effect = lambda _m: client.stop()

        client.run()

        assert scripted.connect.call_count == 2
        assert scripted.sent == [
            {"uuid": client._uuid, "action": "subscribe"},
            {"uuid": client._uuid, "action": "subscribe"},
        ]
        assert writer.write.call_args_list == [call({"n": 1})]

    def test_reintenta_si_falla_el_envio(
        self, connection, writer, monkeypatch
    ):
        connection.connect.side_effect = [None, None]
        connection.send.side_effect = [ConnectionLostError("falló"), None]
        connection.receive.side_effect = [{"n": 1}]
        client = ObserverClient(
            "host", 8080, connection, writer, retry_interval=1
        )
        monkeypatch.setattr(client, "_wait_to_retry", lambda: None)
        writer.write.side_effect = lambda _m: client.stop()

        client.run()

        assert connection.connect.call_count == 2
        assert connection.send.call_count == 2
        assert writer.write.call_args_list == [call({"n": 1})]

    def test_cierra_y_propaga_excepcion_distinta(self, connection):
        connection.connect.side_effect = OSError("arranque fallido")
        client = ObserverClient(
            "host", 8080, connection, Mock(), retry_interval=1
        )
        with pytest.raises(OSError):
            client.run()
        connection.close.assert_called_once()

    def test_propaga_error_de_escritura_y_cierra(self, connection, writer):
        connection.receive.return_value = {"n": 1}
        writer.write.side_effect = OSError("disco lleno")
        client = ObserverClient(
            "host", 8080, connection, writer, retry_interval=1
        )
        with pytest.raises(OSError):
            client.run()
        connection.close.assert_called_once()
        writer.write.assert_called_once_with({"n": 1})

    def test_stop_desde_otro_hilo_termina_run(self, connection):
        connection.connect.side_effect = ConnectionLostError("sin servidor")
        client = ObserverClient(
            "host", 8080, connection, Mock(), retry_interval=30
        )

        hilo = threading.Thread(target=client.run)
        hilo.start()
        time.sleep(0.05)
        client.stop()
        hilo.join(timeout=2)

        assert not hilo.is_alive()
