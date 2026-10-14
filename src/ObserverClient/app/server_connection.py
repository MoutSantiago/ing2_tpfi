"""Módulo encargado de la comunicación TCP con el servidor.

Está separada de ObserverClient para que este no conozca los detalles de la
red y para poder reemplazarla por un mock en los tests.

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import json
import logging
from socket import (
    SHUT_RDWR,
    SO_KEEPALIVE,
    SOL_SOCKET,
    create_connection,
    socket,
)
from typing import Optional, TextIO

from ObserverClient.app.exceptions import ConnectionLostError

CONNECT_TIMEOUT = 5
MAX_LINE = 1024 * 1024

logger = logging.getLogger(__name__)


class ServerConnection:
    """Clase encargada de la comunicación TCP con el servidor.

    Abre y cierra el socket, envía los mensajes y recibe las notificaciones, y
    traduce los errores de bajo nivel del módulo socket a ConnectionLostError.
    """

    _host: str
    """Atributo privado de instancia con el nombre o la dirección del servidor.
    """

    _port: int
    """Atributo privado de instancia con el puerto TCP del servidor."""

    _sock: Optional[socket] = None
    """Atributo privado de instancia con el socket de la conexión.
    Vale None mientras no hay conexión abierta."""

    _reader: Optional[TextIO] = None
    """tributo privado de instancia con el lector de texto asociado al socket
    (sock.makefile), que permite leer los mensajes línea por línea
    Vale None mientras no hay conexión abierta."""

    def __init__(self, host: str, port: int) -> None:
        """Método constructor de la clase.

        Recibe el servidor y el puerto, y los guarda en _host y _port.
        No abre la conexión: eso ocurre en connect().

        Args:
            host (str): Nombre o dirección del servidor.
            port (int): Puerto TCP del servidor.
        """
        self._host = host
        self._port = port
        self._sock = None
        self._reader = None

    @property
    def is_open(self) -> bool:
        """Propiedad de solo lectura.

        Retorna True si hay un socket abierto y False en caso contrario.

        Returns:
            bool: El servidor esta abierto?
        """
        return self._sock is not None

    def connect(self) -> None:
        r"""Abre la conexión TCP con el servidor.

        usa CONNECT_TIMEOUT, pasa el socket a modo bloqueante, activa
        SO_KEEPALIVE y crea _reader (UTF-8, newline="\n").
        Si ya había una conexión abierta, la cierra antes.

        Lanza ConnectionLostError si el servidor no está disponible
        (rechazo, host inalcanzable o timeout).
        """
        self.close()
        try:
            sock = create_connection((self._host, self._port), CONNECT_TIMEOUT)
            sock.settimeout(None)
            sock.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
            self._sock = sock
            self._reader = sock.makefile("r", encoding="utf-8", newline="\n")
        except OSError as error:
            self._sock = None
            self._reader = None
            logger.debug(
                "No se pudo conectar a %s:%d: %s",
                self._host,
                self._port,
                error,
            )
            raise ConnectionLostError(
                f"No se pudo conectar al servidor {self._host}:{self._port}"
            ) from error

        logger.debug("Conexión establecida con %s:%d", self._host, self._port)

    def send(self, message: dict) -> None:
        r"""Serializa el message a JSON de una línea (con ensure_ascii=False).

        Le agrega \n, lo codifica en UTF-8 y lo envía completo con sendall.

        Lanza ConnectionLostError si no hay conexión abierta o si falla el
        envío.

        Args:
            message (dict): Mensaje a enviar.
        """
        if self._sock is None:
            raise ConnectionLostError("No hay conexión abierta")
        data = (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")
        try:
            self._sock.sendall(data)
        except OSError as error:
            logger.warning("Falló el envío del mensaje: %s", error)
            raise ConnectionLostError("Falló el envío del mensaje") from error
        logger.debug("Mensaje enviado: %s", message)

    def receive(self) -> dict:
        r"""Bloquea hasta recibir una línea completa y la retorna como dict.

        Lanza ConnectionLostError si el servidor cerró la conexión
        (lectura vacía), si la línea llegó cortada (sin \n final), si falla el
        socket o si la conexión se cerró localmente con close() mientras
        esperaba (por ejemplo, desde stop() de ObserverClient).
        Lanza ValueError si la línea supera MAX_LINE o no es un objeto JSON
        válido.

        Returns:
            dict: Mensaje recibido.
        """
        if self._reader is None:
            raise ConnectionLostError("No hay conexión abierta")
        try:
            line = self._reader.readline(MAX_LINE + 1)
        except (OSError, ValueError) as error:
            raise ConnectionLostError(
                "Falló la recepción del mensaje"
            ) from error
        if line == "":
            raise ConnectionLostError("El servidor cerró la conexión")
        if not line.endswith("\n"):
            if len(line) > MAX_LINE:
                raise ValueError("La línea recibida supera el tamaño máximo")
            raise ConnectionLostError("La línea llegó cortada (sin \\n final)")
        line = line[:-1]
        if len(line) > MAX_LINE:
            raise ValueError("La línea recibida supera el tamaño máximo")
        message = json.loads(line)
        if not isinstance(message, dict):
            raise ValueError("El mensaje recibido no es un objeto JSON")
        logger.debug("Mensaje recibido del servidor")
        return message

    def close(self) -> None:
        """Cierra _reader y el socket.

        Usa shutdown previo para despertar a un receive bloqueado en otro hilo
        y deja ambos en None.
        Es idempotente: si no había conexión, no hace nada, y nunca lanza
        excepciones.
        """
        if self._sock is None:
            return
        try:
            self._sock.shutdown(SHUT_RDWR)
        except OSError:
            pass
        if self._reader is not None:
            try:
                self._reader.close()
            except OSError:
                pass
            self._reader = None
        try:
            self._sock.close()
        except OSError:
            pass
        self._sock = None
        logger.debug("Conexión con %s:%d cerrada", self._host, self._port)
