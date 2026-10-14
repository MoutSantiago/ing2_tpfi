"""Tests para ServerConnection contra un servidor de prueba local."""

import json
import socket
import threading
import time
from typing import TextIO
from unittest.mock import Mock

import pytest

from ObserverClient.app.exceptions import ConnectionLostError
from ObserverClient.app.server_connection import MAX_LINE, ServerConnection


class FakeServer:
    """Servidor TCP mínimo para las pruebas.

    Escucha en un puerto libre, acepta una única conexión en un hilo y guarda
    el socket aceptado para que el test pueda enviar/recibir/cerrar.
    """

    def __init__(self) -> None:
        self._listener = socket.socket()
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind(("127.0.0.1", 0))
        self._listener.listen(1)
        self.port = self._listener.getsockname()[1]
        self.conn: socket.socket | None = None
        self._thread = threading.Thread(target=self._accept, daemon=True)
        self._thread.start()

    def _accept(self) -> None:
        try:
            self.conn, _ = self._listener.accept()
        except OSError:
            pass

    def wait_accepted(self, timeout: float = 5) -> socket.socket:
        """Espera a que el cliente se conecte y retorna el socket aceptado."""
        deadline = time.monotonic() + timeout
        while self.conn is None:
            if time.monotonic() > deadline:
                raise TimeoutError("El servidor no aceptó la conexión")
            time.sleep(0.01)
        return self.conn

    def reader(self) -> TextIO:
        """Retorna un lector línea por línea del socket aceptado."""
        return self.wait_accepted().makefile(
            "r", encoding="utf-8", newline="\n"
        )

    def send_line(self, text: str) -> None:
        """Envía una línea cruda al cliente."""
        self.wait_accepted().sendall(text.encode("utf-8"))

    def close_conn(self) -> None:
        """Cierra la conexión aceptada."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def close(self) -> None:
        """Cierra todo."""
        self.close_conn()
        self._listener.close()


@pytest.fixture
def server():
    srv = FakeServer()
    yield srv
    srv.close()


@pytest.fixture
def conn(server):
    sc = ServerConnection("127.0.0.1", server.port)
    yield sc
    sc.close()


class TestConnect:
    def test_conecta_e_is_open_cambia(self, server, conn):
        assert not conn.is_open
        conn.connect()
        assert conn.is_open
        server.wait_accepted()

    def test_puerto_sin_servidor_lanza_connection_lost(self):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            free_port = s.getsockname()[1]
        sc = ServerConnection("127.0.0.1", free_port)
        with pytest.raises(ConnectionLostError):
            sc.connect()
        assert not sc.is_open

    def test_reconectar_cierra_la_conexion_previa(self, server, conn):
        conn.connect()
        first = server.wait_accepted()
        # Segundo listener para la nueva conexión.
        server2 = FakeServer()
        try:
            conn._port = server2.port
            conn.connect()
            first.settimeout(2)
            assert first.recv(1) == b""  # la conexión previa fue cerrada
            server2.wait_accepted()
            assert conn.is_open
        finally:
            server2.close()

    def test_activa_keepalive(self, server, conn):
        conn.connect()
        assert (
            conn._sock.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE) != 0
        )


class TestSend:
    def test_envia_json_una_linea(self, server, conn):
        conn.connect()
        conn.send({"action": "subscribe", "id": 1})
        line = server.reader().readline()
        assert line.endswith("\n")
        assert json.loads(line) == {"action": "subscribe", "id": 1}

    def test_caracteres_con_tilde_se_envian_sin_alterarse(self, server, conn):
        conn.connect()
        conn.send({"msg": "señal áéíóú ñ"})
        assert json.loads(server.reader().readline()) == {
            "msg": "señal áéíóú ñ"
        }

    def test_sin_conexion_lanza_connection_lost(self, conn):
        with pytest.raises(ConnectionLostError):
            conn.send({"a": 1})

    def test_envio_fallido_lanza_connection_lost(self, server, conn):
        conn.connect()
        server.wait_accepted()
        server.close_conn()
        # El primer send puede no fallar hasta que el RST llegue;
        # forzamos con varios envíos.
        with pytest.raises(ConnectionLostError):
            for _ in range(100):
                conn.send({"x": "y" * 1000})
                time.sleep(0.01)

    def test_despues_de_close_lanza_connection_lost(self, server, conn):
        conn.connect()
        conn.close()
        with pytest.raises(ConnectionLostError):
            conn.send({"a": 1})


class TestReceive:
    def test_recibe_un_dict(self, server, conn):
        conn.connect()
        server.send_line('{"type": "notify", "value": 42}\n')
        assert conn.receive() == {"type": "notify", "value": 42}

    def test_caracteres_con_tilde_se_reciben_sin_alterarse(self, server, conn):
        conn.connect()
        server.send_line('{"msg": "notificación áéíóú ñ"}\n')
        assert conn.receive() == {"msg": "notificación áéíóú ñ"}

    def test_sin_conexion_lanza_connection_lost(self, conn):
        with pytest.raises(ConnectionLostError):
            conn.receive()

    def test_servidor_cierra_lanza_connection_lost(self, server, conn):
        conn.connect()
        server.wait_accepted()
        server.close_conn()
        with pytest.raises(ConnectionLostError):
            conn.receive()

    def test_linea_cortada_sin_n_final_lanza_connection_lost(
        self, server, conn
    ):
        conn.connect()
        server.send_line('{"a": 1}')  # sin \n
        server.close_conn()
        with pytest.raises(ConnectionLostError):
            conn.receive()

    def test_linea_que_no_es_json_lanza_value_error(self, server, conn):
        conn.connect()
        server.send_line("esto no es json\n")
        with pytest.raises(ValueError):
            conn.receive()
        # La conexión sigue abierta.
        assert conn.is_open
        server.send_line('{"ok": true}\n')
        assert conn.receive() == {"ok": True}

    def test_json_no_objeto_lanza_value_error(self, server, conn):
        conn.connect()
        server.send_line("[1, 2, 3]\n")
        with pytest.raises(ValueError):
            conn.receive()
        assert conn.is_open

    def test_linea_que_supera_max_line_lanza_value_error(self, server, conn):
        conn.connect()
        server.send_line('"' + "x" * (MAX_LINE + 1) + '"\n')
        with pytest.raises(ValueError):
            conn.receive()

    def test_error_de_socket_al_leer_lanza_connection_lost(self, server, conn):
        conn.connect()
        reader = Mock()
        reader.readline.side_effect = OSError("fallo de lectura")
        conn._reader = reader
        with pytest.raises(ConnectionLostError):
            conn.receive()

    def test_error_de_valor_al_leer_lanza_connection_lost(self, server, conn):
        conn.connect()
        reader = Mock()
        reader.readline.side_effect = ValueError("reader cerrado")
        conn._reader = reader
        with pytest.raises(ConnectionLostError):
            conn.receive()

    def test_linea_sin_n_que_supera_max_line_lanza_value_error(
        self, server, conn
    ):
        conn.connect()
        reader = Mock()
        reader.readline.return_value = "x" * (MAX_LINE + 1)
        conn._reader = reader
        with pytest.raises(ValueError):
            conn.receive()

    def test_linea_con_n_que_supera_max_line_lanza_value_error(
        self, server, conn
    ):
        conn.connect()
        reader = Mock()
        reader.readline.return_value = "x" * (MAX_LINE + 1) + "\n"
        conn._reader = reader
        with pytest.raises(ValueError):
            conn.receive()

    def test_close_despierta_receive_bloqueado(self, server, conn):
        conn.connect()
        server.wait_accepted()
        resultado = {}

        def esperar():
            try:
                conn.receive()
            except ConnectionLostError as e:
                resultado["error"] = e

        hilo = threading.Thread(target=esperar)
        hilo.start()
        time.sleep(0.2)
        conn.close()
        hilo.join(timeout=5)
        assert not hilo.is_alive()
        assert isinstance(resultado.get("error"), ConnectionLostError)


class TestClose:
    def test_es_idempotente_sin_conexion(self, conn):
        conn.close()
        conn.close()
        assert not conn.is_open

    def test_cierra_conexion_abierta(self, server, conn):
        conn.connect()
        conn.close()
        assert not conn.is_open
        assert conn._sock is None
        assert conn._reader is None

    def test_se_puede_llamar_dos_veces_con_conexion(self, server, conn):
        conn.connect()
        conn.close()
        conn.close()

    def test_no_lanza_excepciones_aunque_el_socket_falle(self, server, conn):
        conn.connect()
        sock = Mock()
        sock.shutdown.side_effect = OSError("fallo shutdown")
        sock.close.side_effect = OSError("fallo close")
        reader = Mock()
        reader.close.side_effect = OSError("fallo reader")
        conn._sock = sock
        conn._reader = reader
        conn.close()
        assert not conn.is_open
        assert conn._sock is None
        assert conn._reader is None
