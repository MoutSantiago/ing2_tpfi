"""
Gestiona la comunicación TCP con el servidor de SingletonClient.

Cada mensaje se transmite como una línea JSON codificada en UTF-8.
La clase traduce los errores de comunicación a ConnectionLostError.

Ingeniería de Software II - UADER FCyT (2026)
"""

import contextlib
import json
import socket
from typing import Any, Optional, TextIO

from SingletonClient.app.exceptions import ConnectionLostError

# Tiempo máximo para establecer la conexión TCP, en segundos.
CONNECT_TIMEOUT = 5

# Tiempo máximo para recibir una respuesta, en segundos.
DEFAULT_READ_TIMEOUT = 10

# Tamaño máximo permitido para una línea recibida: 16 MiB.
MAX_LINE = 16 * 1024 * 1024


class ServerConnection:
    """Administra una conexión TCP con el servidor."""

    def __init__(
        self,
        host: str,
        port: int,
        read_timeout: Optional[float] = DEFAULT_READ_TIMEOUT,
    ) -> None:
        """Guarda los parámetros sin abrir la conexión."""
        self._host = host
        self._port = port
        self._read_timeout = read_timeout
        self._sock: Optional[socket.socket] = None
        self._reader: Optional[TextIO] = None

    @property
    def is_open(self) -> bool:
        """Indica si existe un socket abierto."""
        return self._sock is not None and self._sock.fileno() != -1

    def connect(self) -> None:
        """Establece la conexión y prepara la lectura de líneas."""
        # Si ya existía una conexión, se cierra antes de abrir otra.
        self.close()

        connection: Optional[socket.socket] = None

        try:
            connection = socket.create_connection(
                (self._host, self._port),
                timeout=CONNECT_TIMEOUT,
            )

            # El socket usa el timeout configurado para la respuesta.
            connection.settimeout(self._read_timeout)

            # El lector interpreta el flujo como texto UTF-8.
            reader = connection.makefile(
                mode="r",
                encoding="utf-8",
                newline="\n",
            )

            self._sock = connection
            self._reader = reader

        except OSError as error:
            # Evita dejar recursos abiertos si falla la preparación.
            if connection is not None:
                connection.close()

            raise ConnectionLostError(
                f"No se pudo conectar con {self._host}:{self._port}."
            ) from error

    def send(self, message: dict) -> None:
        """Envía un diccionario como una única línea JSON."""
        connection = self._sock
        if connection is None or connection.fileno() == -1:
            raise ConnectionLostError(
                "No hay una conexión abierta con el servidor."
            )

        try:
            # ensure_ascii=False conserva los caracteres Unicode.
            line = json.dumps(message, ensure_ascii=False) + "\n"
            data = line.encode("utf-8")

            # sendall garantiza el envío de todos los bytes o un error.
            connection.sendall(data)

        except OSError as error:
            raise ConnectionLostError(
                "Falló el envío de la petición al servidor."
            ) from error

    def receive(self) -> Any:
        """Lee una línea completa y devuelve el valor JSON interpretado."""
        if not self.is_open or self._reader is None:
            raise ConnectionLostError(
                "No hay una conexión abierta con el servidor."
            )

        try:
            # Se permite leer un carácter adicional para detectar
            # una línea que supere el máximo establecido.
            line = self._reader.readline(MAX_LINE + 2)

        except (OSError, UnicodeError) as error:
            raise ConnectionLostError(
                "Falló la recepción de la respuesta del servidor."
            ) from error

        # Una cadena vacía indica que el servidor cerró la conexión.
        if line == "":
            raise ConnectionLostError(
                "El servidor cerró la conexión sin enviar una respuesta."
            )

        # La respuesta debe terminar en salto de línea.
        if not line.endswith("\n"):
            if len(line.rstrip("\r\n")) > MAX_LINE:
                raise ValueError(
                    f"La respuesta supera el máximo de {MAX_LINE} caracteres."
                )

            raise ConnectionLostError(
                "El servidor cerró o interrumpió la respuesta antes "
                "de completar la línea."
            )

        # Se elimina el terminador antes de comprobar el contenido.
        content = line[:-1]

        if content.endswith("\r"):
            content = content[:-1]

        if len(content) > MAX_LINE:
            raise ValueError(
                f"La respuesta supera el máximo de {MAX_LINE} caracteres."
            )

        try:
            return json.loads(content)
        except json.JSONDecodeError as error:
            raise ValueError(
                "La respuesta del servidor no contiene un JSON válido."
            ) from error

    def close(self) -> None:
        """Cierra los recursos disponibles sin propagar excepciones."""
        reader = self._reader
        connection = self._sock

        # Se actualiza el estado primero para que close sea idempotente.
        self._reader = None
        self._sock = None

        if reader is not None:
            with contextlib.suppress(OSError):
                reader.close()

        if connection is not None:
            with contextlib.suppress(OSError):
                connection.close()
